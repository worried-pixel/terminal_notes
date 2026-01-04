# recovery_system.py
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from terminal_notes_core import Note  # 🆕 ADD THIS IMPORT

class RecoverySystem:
    def __init__(self, manager):
        self.manager = manager
        self.recovery_dir = Path(__file__).parent / ".recovery"  # Same directory as the script
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
    
    def get_recovery_filename(self, note_uuid, note_title, is_file_note=False, file_extension=None):
        """Generate recovery filename using last 6 chars of UUID"""
        uuid_part = str(note_uuid)[-6:]
        safe_title = "".join(c for c in note_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:30]  # Limit length
        
        if is_file_note and file_extension:
            return f"{safe_title}_{uuid_part}.{file_extension}"
        else:
            return f"{safe_title}_{uuid_part}"
    
    def save_recovery_file(self, note_uuid, parent_notebook_uuid, content, note_title, 
                          is_file_note=False, file_extension=None):
        """Save autosave recovery file"""
    
        def log(message):
            with open("/tmp/terminal_notes_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()}: {message}\n")
    
        filename = self.get_recovery_filename(note_uuid, note_title, is_file_note, file_extension)
        recovery_path = self.recovery_dir / filename
    
        log(f"SAVE_RECOVERY: Creating {recovery_path}")
    
        recovery_data = {
            "note_uuid": str(note_uuid),
            "parent_notebook_uuid": str(parent_notebook_uuid),
            "content": content,
            "is_file_note": is_file_note,
            "file_extension": file_extension,
            "note_title": note_title,
            "last_updated": datetime.now().isoformat()
        }
    
        try:
            # Atomic write - write to temp then rename
            temp_path = recovery_path.with_suffix('.tmp')
            log(f"SAVE_RECOVERY: Writing to temp file {temp_path}")
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(recovery_data, f, indent=2)
            temp_path.rename(recovery_path)
            log(f"SAVE_RECOVERY: Successfully saved {recovery_path}")
            return True
        except Exception as e:
            log(f"SAVE_RECOVERY ERROR: {e}")
            return False
    
    def get_recovery_files_for_notebook(self, notebook_uuid):
        """Get all recovery files for a specific notebook"""
        notebook_recoveries = []
        
        for recovery_file in self.recovery_dir.glob('*'):
            if recovery_file.is_file() and not recovery_file.name.endswith('.tmp'):
                try:
                    with open(recovery_file, 'r', encoding='utf-8') as f:
                        recovery_data = json.load(f)
                    
                    if recovery_data.get('parent_notebook_uuid') == str(notebook_uuid):
                        notebook_recoveries.append((recovery_file, recovery_data))
                except (json.JSONDecodeError, KeyError):
                    continue  # Skip corrupted files
        
        return notebook_recoveries
    
    def recover_notebook_content(self, notebook):
        recovered_count = 0
        recovery_files = self.get_recovery_files_for_notebook(notebook.id)
    
        for recovery_file, recovery_data in recovery_files:
            try:
                note_uuid = recovery_data['note_uuid']
                content = recovery_data['content']
                note_title = recovery_data['note_title']
                is_file_note = recovery_data['is_file_note']
                file_extension = recovery_data['file_extension']
            
                # Check if this is a creation recovery or modification recovery
                existing_note, existing_notebook = self.manager.find_note_by_id(None, note_uuid)
            
                if existing_note:
                    # Modification recovery
                    recovery_time = datetime.fromisoformat(recovery_data['last_updated'])
                    if recovery_time > existing_note.updated:
                        old_content = existing_note.content
                        existing_note.content = content
                        existing_note.updated = datetime.now()
                    
                        # 🆕 SAVE SILENTLY - don't trigger navigation
                        self._save_notebook_silently(existing_notebook)
                    
                        # Commit the recovery
                        try:
                            root_notebook = self.manager._find_root_notebook(existing_notebook)
                            git_manager = self.manager.get_git_manager(root_notebook.name)
                            git_manager.commit_note_edit(
                                note_uuid, note_title, root_notebook.name, 
                                old_content, content
                            )
                        except Exception:
                            pass
                    
                        recovered_count += 1
                else:
                    # Creation recovery
                    if content.strip():
                        new_note = Note(
                            note_title, 
                            content, 
                            note_id=note_uuid,
                            created_with="vim"
                        )
                        if is_file_note:
                            new_note.file_extension = file_extension
                    
                        notebook.notes.append(new_note)
                    
                        # 🆕 SAVE SILENTLY - don't trigger navigation
                        self._save_notebook_silently(notebook)
                    
                        # Commit the creation
                        try:
                            root_notebook = self.manager._find_root_notebook(notebook)
                            git_manager = self.manager.get_git_manager(root_notebook.name)
                            if is_file_note:
                                git_manager.commit_file_creation(
                                    note_uuid, note_title, root_notebook.name, 
                                    file_extension, content
                                )
                            else:
                                git_manager.commit_note_creation(
                                    note_uuid, note_title, root_notebook.name, 
                                    "vim", content
                                )
                        except Exception:
                            pass
                    
                        recovered_count += 1
            
                # Clean up recovery file after successful recovery
                recovery_file.unlink()
            
            except Exception as e:
                print(f"Recovery error for {recovery_file}: {e}")
                continue
    
        return recovered_count
    
    def _save_notebook_silently(self, notebook):
        """Save notebook without triggering navigation events"""
        # 🆕 DIRECT SAVE without going through the full manager.save_data()
        folder_path = self.manager.get_notebook_folder_path(notebook.name)
        structure_file, notes_file, files_file = self.manager.get_notebook_file_paths(notebook.name)

        # Save structure (metadata only)
        structure_data = notebook.to_dict()
        with open(structure_file, "w") as f:
            json.dump(structure_data, f, indent=2)

        # Save content files directly
        notes_map = {}
        files_map = {}
        self.manager._extract_file_content_from_notebook(notebook, notes_map, files_map)

        with open(notes_file, "w") as f:
            json.dump(notes_map, f, indent=2)

        with open(files_file, "w") as f:
            json.dump(files_map, f, indent=2)
    
    def cleanup_stale_recovery_files(self, older_than_hours=24):
        """Clean up old recovery files"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        for recovery_file in self.recovery_dir.glob('*'):
            if recovery_file.is_file():
                if recovery_file.stat().st_mtime < cutoff_time:
                    recovery_file.unlink()