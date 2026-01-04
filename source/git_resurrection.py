#!/usr/bin/env python3
import sys

sys.dont_write_bytecode = True
import subprocess
import json
import re
import tempfile
import os
from datetime import datetime

class GitHistoryMiner:
    def __init__(self, note_manager):
        self.manager = note_manager
        self.temp_files = []
        
    def find_deleted_items(self, query):
        deleted_items = []
        seen_ids = set()

        for notebook in self.manager.notebooks:
            notebook_path = self.manager.get_notebook_folder_path(notebook.name)
        
            # 🆕 FIX: Only search for DELETED items specifically
            cmd = [
                "git", "log", "--oneline", "-i", "--grep", f"DELETED.*{query}",
                "--all", "--pretty=format:%H %s"
            ]
        
            try:
                result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.splitlines():
                        if line.strip():
                            commit_hash, message = line.split(' ', 1)
                        
                            item_id, target_commit = self._extract_item_id_and_commit(notebook_path, commit_hash, message)
                        
                            if item_id and target_commit and item_id not in seen_ids:
                                seen_ids.add(item_id)
                                item_data = self._create_temp_json_for_item(
                                    notebook_path, item_id, target_commit, message
                                )
                                if item_data:
                                    deleted_items.append(item_data)
                                
            except Exception as e:
                continue
            
        return deleted_items

    def _find_id_by_name_in_commit(self, notebook_path, commit_hash, item_name):
        try:
            cmd = ["git", "show", f"{commit_hash}:structure.json"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
        
            if result.returncode != 0:
                return None
            
            structure_data = json.loads(result.stdout)
        
            def search_recursive(data, target_name):
                if isinstance(data, dict):
                    # Search in notes
                    for note in data.get('notes', []):
                        if note.get('title', '').lower() == target_name.lower():
                            return note.get('id')
                    # Search in subnotebooks
                    for sub_nb in data.get('subnotebooks', []):
                        if sub_nb.get('name', '').lower() == target_name.lower():
                            return sub_nb.get('id')
                        result = search_recursive(sub_nb, target_name)
                        if result:
                            return result
                elif isinstance(data, list):
                    for item in data:
                        result = search_recursive(item, target_name)
                        if result:
                            return result
                return None
            
            found_id = search_recursive(structure_data, item_name)
            return found_id
        
        except Exception as e:
            return None
    def _extract_item_id_and_commit(self, notebook_path, commit_hash, message):
        is_deletion = "DELETED" in message.upper()
    
        if is_deletion:
            # For deletion, get the commit BEFORE to find the item
            before_commit = self._get_commit_before(notebook_path, commit_hash)
            if not before_commit:
                return None, None
            
            # Extract name from deletion message
            name_match = re.search(r'DELETED\s+\w+:\s*([^|]+)', message)
            if not name_match:
                return None, None
            
            item_name = name_match.group(1).strip()
        
            # Search directly in the before_commit
            item_id = self._find_id_by_name_in_commit(notebook_path, before_commit, item_name)
        
            return item_id, before_commit
    
        return None, None
    
    def _find_creation_uuid(self, notebook_path, item_name):
        """Find the UUID from the creation commit of an item"""
        # Search for creation commits of this item
        cmd = [
            "git", "log", "--oneline", "-i", "--grep", f"CREATED.*{re.escape(item_name)}",
            "--all", "--pretty=format:%H %s"
        ]
    
        try:
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                # Get the first creation commit (most recent)
                first_line = result.stdout.splitlines()[0]
                commit_hash, message = first_line.split(' ', 1)
                # Extract UUID from this creation commit
                return self._find_id_by_name_in_commit(notebook_path, commit_hash, item_name)
        except Exception as e:
            return None

    def _get_commit_before(self, notebook_path, commit_hash):
        try:
            cmd = ["git", "log", "-1", "--pretty=format:%H", f"{commit_hash}^"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            cmd = ["git", "log", "-1", "--before", commit_hash, "--pretty=format:%H", "--all"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
        except Exception:
            pass
        
        return None

    def _find_id_by_name_in_commit(self, notebook_path, commit_hash, item_name):
        try:
            cmd = ["git", "show", f"{commit_hash}:structure.json"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
        
            if result.returncode != 0:
                return None
            
            structure_data = json.loads(result.stdout)
        
            def search_recursive(data, target_name):
                if isinstance(data, dict):
                    # Search in notes
                    for note in data.get('notes', []):
                        if note.get('title', '').lower() == target_name.lower():
                            return note.get('id')
                    # Search in subnotebooks
                    for sub_nb in data.get('subnotebooks', []):
                        if sub_nb.get('name', '').lower() == target_name.lower():
                            return sub_nb.get('id')
                        result = search_recursive(sub_nb, target_name)
                        if result:
                            return result
                elif isinstance(data, list):
                    for item in data:
                        result = search_recursive(item, target_name)
                        if result:
                            return result
                return None
            
            found_id = search_recursive(structure_data, item_name)
            return found_id
        
        except Exception as e:
            return None

    def _create_temp_json_for_item(self, notebook_path, item_id, target_commit, message=""):
        try:
        
            structure_data = self._get_historical_json(notebook_path, target_commit, "structure.json")           
        
            if not structure_data:
                return None
    
            item_info = self._find_item_in_structure(structure_data, item_id)
        
            if not item_info:
                return None
        
            # Determine item type
            if 'name' in item_info:
                item_title = item_info['name']
                is_file_note = False
                is_subnotebook = True
            else:
                item_title = item_info.get('title', 'Unknown')
                is_file_note = 'file_extension' in item_info and item_info['file_extension'] is not None
                is_subnotebook = False

            temp_dir = tempfile.mkdtemp(prefix="resurrected_")
            self.temp_files.append(temp_dir)
    
            # Build structure
            temp_structure = self._create_minimal_structure(structure_data, item_id, item_info)
            # Save structure
            structure_path = os.path.join(temp_dir, "structure.json")
            with open(structure_path, "w") as f:
                json.dump(temp_structure, f, indent=2)

            
            
            # 🆕 DETAILED DEBUG: Check what we're actually writing
            if is_subnotebook:
                # For subnotebooks: load ALL content from the hierarchy
                notes_data = self._get_historical_json(notebook_path, target_commit, "notes.json") or {}
                files_data = self._get_historical_json(notebook_path, target_commit, "files.json") or {}
    
                notebook_notes = {}
                notebook_files = {}
                self._collect_subnotebook_content(item_info, notes_data, files_data, notebook_notes, notebook_files)
    
    
                
    
                # Write notes.json
                notes_path = os.path.join(temp_dir, "notes.json")
                with open(notes_path, "w") as f:
                    json.dump(notebook_notes, f, indent=2)
                
    
                # Write files.json  
                files_path = os.path.join(temp_dir, "files.json")
                with open(files_path, "w") as f:
                    json.dump(notebook_files, f, indent=2)
                
                
            else:
                # For notes: load individual content
                content_file = "files.json" if is_file_note else "notes.json"
                content_data = self._get_historical_json(notebook_path, target_commit, content_file)
                content = content_data.get(item_id, "") if content_data else ""
            
                temp_content = {item_id: content}
                content_filename = "files.json" if is_file_note else "notes.json"
                with open(os.path.join(temp_dir, content_filename), "w") as f:
                    json.dump(temp_content, f, indent=2)
            
                # 🆕 FIX: Only create counterpart file if it doesn't exist or is needed
                counterpart_filename = "notes.json" if is_file_note else "files.json"
                counterpart_path = os.path.join(temp_dir, counterpart_filename)
                if not os.path.exists(counterpart_path):
                    with open(counterpart_path, "w") as f:
                        json.dump({}, f, indent=2)
    
            # Save structure
            with open(os.path.join(temp_dir, "structure.json"), "w") as f:
                json.dump(temp_structure, f, indent=2)
                
    
            return {
                'type': 'resurrected_note',
                'title': item_title,
                'content': content if not is_subnotebook else "",
                'file_extension': item_info.get('file_extension'),
                'created_with': item_info.get('created_with', 'unknown'),
                'uuid': item_id,
                'notebook_path': notebook_path,
                'temp_dir': temp_dir,
                'item_info': item_info,
                'commit_message': message,
                'is_file_note': is_file_note,
                'is_subnotebook': is_subnotebook
            }
                
        except Exception as e:
            
            return None

    def _collect_subnotebook_content(self, subnotebook, all_notes, all_files, collected_notes, collected_files):
        """Recursively collect all notes and files from a subnotebook hierarchy"""
        # Collect notes from this subnotebook
        for note in subnotebook.get('notes', []):
            note_id = note.get('id')
        
            if note_id in all_notes:
                collected_notes[note_id] = all_notes[note_id]
            elif note_id in all_files:
                collected_files[note_id] = all_files[note_id]
    
        # Recursively collect from subnotebooks
        for child_subnotebook in subnotebook.get('subnotebooks', []):
            self._collect_subnotebook_content(child_subnotebook, all_notes, all_files, collected_notes, collected_files)

    def _create_minimal_structure(self, full_structure, target_uuid, target_item):
        """Create minimal structure.json containing the resurrected item - FIXED VERSION"""
        def find_and_build_hierarchy(data, target_uuid, current_path):
            if isinstance(data, dict) and 'id' in data:
                if data.get('id') == target_uuid:
                    # 🆕 FIX: If this is a subnotebook, return it AS-IS with all its content
                    if 'subnotebooks' in data or 'notes' in data:
                        return data  # Return the complete subnotebook structure
                    else:
                        # This is a regular notebook containing our target
                        minimal_notebook = {
                            'id': current_path[-1]['id'] if current_path else data.get('id'),
                            'name': current_path[-1]['name'] if current_path else 'Resurrected',
                            'parent_id': None,
                            'notes': [target_item],
                            'subnotebooks': []
                        }
                        return minimal_notebook
            
                # Search in notes
                for note in data.get('notes', []):
                    if note.get('id') == target_uuid:
                        # Found the note - build parent notebook
                        minimal_notebook = {
                            'id': data.get('id'),
                            'name': data.get('name'),
                            'parent_id': data.get('parent_id'),
                            'notes': [target_item],
                            'subnotebooks': []
                        }
                        return minimal_notebook
            
                # Search in subnotebooks
                for sub_nb in data.get('subnotebooks', []):
                    result = find_and_build_hierarchy(sub_nb, target_uuid, current_path + [data])
                    if result:
                        return result
        
            elif isinstance(data, list):
                for item in data:
                    result = find_and_build_hierarchy(item, target_uuid, current_path)
                    if result:
                        return result
        
            return None
    
        minimal_notebook = find_and_build_hierarchy(full_structure, target_uuid, [])
    
        if minimal_notebook:
            # 🆕 FIX: Check if what we found is already a complete subnotebook
            if 'subnotebooks' in minimal_notebook or 'notes' in minimal_notebook:
                # This is a complete subnotebook - return it as-is
                return {
                    'notebooks': [minimal_notebook],
                    'resurrected': True,
                    'resurrected_at': datetime.now().isoformat()
                }
            else:
                # This is a minimal notebook wrapper
                return {
                    'notebooks': [minimal_notebook],
                    'resurrected': True,
                    'resurrected_at': datetime.now().isoformat()
                }
        else:
            # 🆕 FIX: Fallback that preserves subnotebook structure
            if 'subnotebooks' in target_item or 'notes' in target_item:
                # This is a subnotebook - return it with complete structure
                return {
                    'notebooks': [target_item],
                    'resurrected': True,
                    'resurrected_at': datetime.now().isoformat()
                }
            else:
                # This is a regular note
                return {
                    'notebooks': [{
                        'id': 'resurrected_notebook',
                        'name': 'Resurrected Items',
                        'parent_id': None,
                        'notes': [target_item],
                        'subnotebooks': []
                    }],
                    'resurrected': True,
                    'resurrected_at': datetime.now().isoformat()
                }
                
    def _get_historical_json(self, notebook_path, commit_hash, filename):
        try:
            cmd = ["git", "show", f"{commit_hash}:{filename}"]
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None

    def _find_item_in_structure(self, structure_data, target_uuid):
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

    def cleanup_temp_files(self):
        for temp_dir in self.temp_files:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        self.temp_files = []
        
    ## TIMELINE
    # Add to git_resurrection.py - GitHistoryMiner class
    def get_note_timeline(self, note_id, notebook_id):
        """Get all historical versions of a specific note"""
        timeline_items = []
    
        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            return timeline_items
        
        notebook_path = self.manager.get_notebook_folder_path(notebook.name)
    
        # 🆕 CHANGE: Use FULL commit messages with %B
        cmd = [
            "git", "log", "--all", 
            "--pretty=format:%H|%ai|%BENDOFCOMMIT",  # %B for full message + delimiter
            "--grep", note_id
        ]
    
        try:
            result = subprocess.run(cmd, cwd=notebook_path, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                # Split by our custom delimiter
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
                                    timeline_items.append({
                                        'commit_hash': commit_hash,
                                        'date': date_obj,
                                        'message': full_message.strip(),
                                        'note_id': note_id,
                                        'notebook_path': notebook_path
                                    })
                                except ValueError:
                                    timeline_items.append({
                                        'commit_hash': commit_hash,
                                        'date': datetime.now(),
                                        'message': full_message.strip(),
                                        'note_id': note_id,
                                        'notebook_path': notebook_path
                                    })
        except Exception as e:
            print(f"Timeline error: {e}")
        
        return sorted(timeline_items, key=lambda x: x['date'], reverse=True)
    
    def _create_complete_subnotebook_structure(self, full_structure, target_uuid, target_subnotebook):
        """Create complete structure for a subnotebook including all its content"""
        return {
            'notebooks': [target_subnotebook],  # The subnotebook with ALL its nested content
            'resurrected': True,
            'resurrected_at': datetime.now().isoformat()
        }

    def _collect_subnotebook_content(self, subnotebook, all_notes, all_files, collected_notes, collected_files):
        """Recursively collect all notes and files from a subnotebook hierarchy"""
        # Collect notes from this subnotebook
        for note in subnotebook.get('notes', []):
            note_id = note.get('id')
            if note_id in all_notes:
                collected_notes[note_id] = all_notes[note_id]
            elif note_id in all_files:
                collected_files[note_id] = all_files[note_id]
    
        # Recursively collect from subnotebooks
        for child_subnotebook in subnotebook.get('subnotebooks', []):
            self._collect_subnotebook_content(child_subnotebook, all_notes, all_files, collected_notes, collected_files)
    
    def _build_minimal_structure(self, full_structure, target_uuid, target_item):
        """Build minimal structure containing only the target subnotebook"""
        return {
            'notebooks': [target_item],  # Just the subnotebook itself
            'resurrected': True,
            'resurrected_at': datetime.now().isoformat()
        }