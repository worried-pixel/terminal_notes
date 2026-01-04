# timeline_engine.py
#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import os
import json
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

class TimelineEngine:
    def __init__(self, note_manager):
        self.manager = note_manager
        self.temp_dirs = []
    
    def create_version_at_commit(self, item_uuid, notebook_path, commit_hash, commit_message=""):
        """
        Create a temporary JSON structure for ANY item at a specific commit
        Works for: notes, files, subnotebooks, notebooks
        """
        
    
        try:
            # Get the complete structure at this commit
            structure_data = self._get_historical_json(notebook_path, commit_hash, "structure.json")
            
        
            if not structure_data:
                
                return None
        
            # Find the item in the historical structure
            item_info = self._find_item_in_structure(structure_data, item_uuid)
            
        
            if not item_info:
                
                return None
        
            # Determine item type and handle accordingly
            item_type = self._determine_item_type(item_info)
            
        
            if item_type in ['note', 'file']:
                result = self._create_note_version(item_uuid, item_info, notebook_path, commit_hash, commit_message, item_type)
                
                return result
            elif item_type in ['notebook', 'subnotebook']:
                result = self._create_notebook_version(item_uuid, item_info, notebook_path, commit_hash, commit_message, structure_data)
                
                return result
            else:
                return None
                
        except Exception as e:
            print(f"Error creating version: {str(e)}")
            return None
    
    def _determine_item_type(self, item_info):
        """Determine what type of item this is"""
        if 'file_extension' in item_info and item_info['file_extension'] is not None:
            return 'file'
        elif 'title' in item_info and ('parent_id' in item_info or 'id' in item_info):
            return 'note'
        elif 'subnotebooks' in item_info or 'notes' in item_info:
            if 'parent_id' in item_info and item_info['parent_id'] is not None:
                return 'subnotebook'
            else:
                return 'notebook'
        return 'unknown'
    
    def _create_note_version(self, item_uuid, item_info, notebook_path, commit_hash, commit_message, item_type):
        """Create temporary structure for a note/file at specific commit"""
        try:
            # Get content from appropriate JSON file
            content_file = "files.json" if item_type == 'file' else "notes.json"
            content_data = self._get_historical_json(notebook_path, commit_hash, content_file)
            content = content_data.get(item_uuid, "") if content_data else ""
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"timeline_{item_uuid[:8]}_")
            self.temp_dirs.append(temp_dir)
            
            # Build complete hierarchy for this item
            full_structure = self._get_historical_json(notebook_path, commit_hash, "structure.json")
            timeline_structure = self._build_complete_hierarchy(full_structure, item_uuid, item_info)
            
            # Save structure
            with open(os.path.join(temp_dir, "structure.json"), "w") as f:
                json.dump(timeline_structure, f, indent=2)
            
            # Save content
            content_filename = "files.json" if item_type == 'file' else "notes.json"
            temp_content = {item_uuid: content}
            with open(os.path.join(temp_dir, content_filename), "w") as f:
                json.dump(temp_content, f, indent=2)
            
            # Empty counterpart file
            counterpart_filename = "notes.json" if item_type == 'file' else "files.json"
            with open(os.path.join(temp_dir, counterpart_filename), "w") as f:
                json.dump({}, f, indent=2)
            
            return {
                'type': 'timeline_version',
                'item_type': item_type,
                'title': item_info.get('title', 'Unknown'),
                'content': content,
                'file_extension': item_info.get('file_extension'),
                'uuid': item_uuid,
                'notebook_path': notebook_path,
                'temp_dir': temp_dir,
                'commit_hash': commit_hash,
                'commit_message': commit_message,
                'item_info': item_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error creating note version: {str(e)}")
            return None
    
    def _create_notebook_version(self, item_uuid, item_info, notebook_path, commit_hash, commit_message, structure_data):
        """Create temporary structure for a notebook/subnotebook at specific commit"""
        try:
            temp_dir = tempfile.mkdtemp(prefix=f"timeline_nb_{item_uuid[:8]}_")
            self.temp_dirs.append(temp_dir)
            
            # Extract this notebook and ALL its content from the full structure
            notebook_structure = self._extract_notebook_hierarchy(structure_data, item_uuid)
            
            if not notebook_structure:
                return None
            
            # Get ALL notes and files content for this notebook
            notes_data = self._get_historical_json(notebook_path, commit_hash, "notes.json") or {}
            files_data = self._get_historical_json(notebook_path, commit_hash, "files.json") or {}
            
            # Filter content to only include items from this notebook hierarchy
            notebook_notes = {}
            notebook_files = {}
            
            self._collect_notebook_content(notebook_structure, notes_data, files_data, notebook_notes, notebook_files)
            
            # Save structure
            with open(os.path.join(temp_dir, "structure.json"), "w") as f:
                json.dump(notebook_structure, f, indent=2)
            
            # Save content files
            with open(os.path.join(temp_dir, "notes.json"), "w") as f:
                json.dump(notebook_notes, f, indent=2)
            
            with open(os.path.join(temp_dir, "files.json"), "w") as f:
                json.dump(notebook_files, f, indent=2)
            
            return {
                'type': 'timeline_version',
                'item_type': 'notebook',
                'title': item_info.get('name', 'Unknown Notebook'),
                'uuid': item_uuid,
                'notebook_path': notebook_path,
                'temp_dir': temp_dir,
                'commit_hash': commit_hash,
                'commit_message': commit_message,
                'item_info': item_info,
                'note_count': len(notebook_notes),
                'file_count': len(notebook_files),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error creating notebook version: {str(e)}")
            return None
    
    def _build_complete_hierarchy(self, full_structure, target_uuid, target_item):
        """Build complete notebook hierarchy containing the target item"""
        def find_hierarchy(data, target_uuid, current_path):
            if isinstance(data, dict) and 'id' in data:
                if data.get('id') == target_uuid:
                    # Found the container notebook
                    return {
                        'notebooks': [{
                            'id': data.get('id'),
                            'name': data.get('name', 'Resurrected'),
                            'parent_id': data.get('parent_id'),
                            'notes': data.get('notes', []),
                            'subnotebooks': data.get('subnotebooks', [])
                        }],
                        'timeline_version': True,
                        'reconstructed_at': datetime.now().isoformat()
                    }
                
                # Search in subnotebooks
                for sub_nb in data.get('subnotebooks', []):
                    result = find_hierarchy(sub_nb, target_uuid, current_path + [data])
                    if result:
                        return result
            
            elif isinstance(data, list):
                for item in data:
                    result = find_hierarchy(item, target_uuid, current_path)
                    if result:
                        return result
            
            return None
        
        result = find_hierarchy(full_structure, target_uuid, [])
        
        if not result:
            # Fallback: create minimal structure with just the item
            result = {
                'notebooks': [{
                    'id': 'timeline_notebook',
                    'name': 'Historical Version',
                    'parent_id': None,
                    'notes': [target_item] if target_item else [],
                    'subnotebooks': []
                }],
                'timeline_version': True,
                'reconstructed_at': datetime.now().isoformat()
            }
        
        return result
    
    def _extract_notebook_hierarchy(self, full_structure, notebook_uuid):
        """Extract complete notebook hierarchy with all subnotebooks and notes"""
        def find_and_extract(data, target_uuid):
            if isinstance(data, dict) and 'id' in data:
                if data.get('id') == target_uuid:
                    return data
                
                for sub_nb in data.get('subnotebooks', []):
                    result = find_and_extract(sub_nb, target_uuid)
                    if result:
                        return result
            
            elif isinstance(data, list):
                for item in data:
                    result = find_and_extract(item, target_uuid)
                    if result:
                        return result
            
            return None
        
        notebook_data = find_and_extract(full_structure, notebook_uuid)
        
        if notebook_data:
            return {
                'notebooks': [notebook_data],
                'timeline_version': True,
                'reconstructed_at': datetime.now().isoformat()
            }
        
        return None
    
    def _collect_notebook_content(self, notebook_structure, all_notes, all_files, notebook_notes, notebook_files):
        """Collect all notes and files content for a notebook hierarchy"""
        def extract_from_notebook(notebook):
            # Extract notes
            for note in notebook.get('notes', []):
                note_id = note.get('id')
                if note_id in all_notes:
                    notebook_notes[note_id] = all_notes[note_id]
                elif note_id in all_files:
                    notebook_files[note_id] = all_files[note_id]
            
            # Recursively process subnotebooks
            for sub_nb in notebook.get('subnotebooks', []):
                extract_from_notebook(sub_nb)
        
        for notebook in notebook_structure.get('notebooks', []):
            extract_from_notebook(notebook)
    
    def _get_historical_json(self, notebook_path, commit_hash, filename):
        """Get JSON file content from specific commit"""
        try:
            cmd = ["git", "show", f"{commit_hash}:{filename}"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None
    
    def _find_item_in_structure(self, structure_data, target_uuid):
        """Find any item by UUID in structure"""
        def search_recursive(data):
            if isinstance(data, dict):
                if data.get('id') == target_uuid:
                    return data
                
                for note in data.get('notes', []):
                    if note.get('id') == target_uuid:
                        return note
                
                for sub_nb in data.get('subnotebooks', []):
                    result = search_recursive(sub_nb)
                    if result:
                        return result
            
            elif isinstance(data, list):
                for item in data:
                    result = search_recursive(item)
                    if result:
                        return result
            
            return None
        
        return search_recursive(structure_data)
    
    def get_item_timeline(self, item_uuid, notebook_id):
        """Get complete timeline for any item"""
        timeline_versions = []
    
        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            return timeline_versions
       
        root_notebook = self.manager._find_root_notebook(notebook)
        notebook_path = self.manager.get_notebook_folder_path(root_notebook.name) if root_notebook else self.manager.get_notebook_folder_path(notebook.name)
    
        # Get all commits mentioning this UUID
        cmd = [
            "git", "log", "--all", 
            "--pretty=format:%H|%ai|%BENDOFCOMMIT",
            "--grep", item_uuid
        ]
    
        try:
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
        
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('ENDOFCOMMIT')
            
                for commit in commits:
                    if commit.strip():
                        lines = commit.strip().splitlines()
                        if len(lines) >= 2:
                            first_line = lines[0]
                            rest_of_message = '\n'.join(lines[1:])
                        
                            parts = first_line.split('|', 2)
                            if len(parts) >= 3:
                                commit_hash, date_str, subject = parts
                                full_message = subject + '\n' + rest_of_message
                            
                                try:
                                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
                                
                                    # Create version for this commit
                                    version_data = self.create_version_at_commit(
                                        item_uuid, notebook_path, commit_hash, full_message.strip()
                                    )
                                
                                    if version_data:
                                        version_data['date'] = date_obj
                                        timeline_versions.append(version_data)
                                    
                                except ValueError:
                                    # Fallback for date parsing
                                    version_data = self.create_version_at_commit(
                                        item_uuid, notebook_path, commit_hash, full_message.strip()
                                    )
                                    if version_data:
                                        version_data['date'] = datetime.now()
                                        timeline_versions.append(version_data)
                                    
        except Exception as e:
            print(f"Timeline error: {e}")
    
        return sorted(timeline_versions, key=lambda x: x['date'], reverse=True)
    
    def create_current_version(self, item_uuid, notebook_id):
        """Create timeline version for CURRENT state (no Git commit needed)"""
        try:
            # Find the item in current structure
            notebook = self.manager.find_notebook_by_id(notebook_id)
            if not notebook:
                return None
            
            # This would use the manager to build the current state
            # Implementation depends on your current manager structure
            return self._build_current_state(item_uuid, notebook)
            
        except Exception as e:
            print(f"Error creating current version: {str(e)}")
            return None
    
    def _build_current_state(self, item_uuid, notebook):
        """Build current state without Git (using live data)"""
        # This would integrate with your existing manager
        # to create the same JSON structure but from current data
        # Similar to _create_note_version but using manager methods
        
        # Placeholder - you'd implement based on your manager's capabilities
        return None
    
    def cleanup(self):
        """Clean up all temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        self.temp_dirs = []