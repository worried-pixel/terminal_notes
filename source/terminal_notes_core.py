#!/usr/bin/env python3
import sys

sys.dont_write_bytecode = True
import os
import json
import subprocess
import tempfile
import shutil
import readline
import traceback
import uuid
import re
from datetime import datetime
from pathlib import Path
from git_manager import GitManager


def ensure_uuid(id_value):
    """
    Keeps your old timestamp IDs working,
    but generates a UUID for new items automatically.
    """
    if not id_value:
        return str(uuid.uuid4())
    # If it's an old timestamp ID (all digits, less than 20 chars), keep it
    if re.match(r"^\d{8,20}$", str(id_value)):
        return id_value
    # If it's already a UUID, keep it
    return str(id_value)


class Note:
    def __init__(self, title, content="", note_id=None, created_with="internal"):
        self.id = ensure_uuid(note_id or datetime.now().strftime("%Y%m%d%H%M%S"))
        self.title = title
        self.content = content
        self.created = datetime.now()
        self.updated = datetime.now()
        self.created_with = created_with
        self.file_extension = None

    def to_dict(self):
        data = {
            "id": self.id,
            "title": self.title,
            # CONTENT REMOVED - now stored in content.json only
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "created_with": self.created_with,
        }
        if self.file_extension:
            data["file_extension"] = self.file_extension
        return data

    @classmethod
    def from_dict(cls, data):
        # Start with empty content - will be filled from content.json
        note = cls(
            data["title"],
            "",  # Empty content - will be loaded from content.json
            data["id"],
            data.get("created_with", "internal"),
        )
        note.created = datetime.fromisoformat(data["created"])
        note.updated = datetime.fromisoformat(data["updated"])
        note.file_extension = data.get("file_extension")
        return note

    @property
    def is_file_note(self):
        return self.file_extension is not None

class Notebook:
    def __init__(self, name, parent_id=None, notebook_id=None):
        self.id = ensure_uuid(notebook_id or datetime.now().strftime("%Y%m%d%H%M%S"))
        self.name = name
        self.parent_id = parent_id
        self.notes = []
        self.subnotebooks = []
        self.custom_path = None  # 🆕 Custom location storage

    def get_total_note_count(self):
        count = len(self.notes)
        for sub_nb in self.subnotebooks:
            count += sub_nb.get_total_note_count()
        return count

    def get_total_subnotebook_count(self):
        count = len(self.subnotebooks)
        for sub_nb in self.subnotebooks:
            count += sub_nb.get_total_subnotebook_count()
        return count
    

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "notes": [note.to_dict() for note in self.notes],
            "subnotebooks": [nb.to_dict() for nb in self.subnotebooks],
        }
        # 🆕 Save custom path if exists - FIXED POSITION
        if hasattr(self, 'custom_path') and self.custom_path:
            data["custom_path"] = self.custom_path
        return data


    @classmethod
    def from_dict(cls, data):
        notebook = cls(data["name"], data["parent_id"], data["id"])
        # 🆕 FIX: Skip items that don't have 'title' field (subnotebooks)
        notebook.notes = []
        for note_data in data["notes"]:
            if 'title' in note_data:  # Only load actual notes
                notebook.notes.append(Note.from_dict(note_data))
        notebook.subnotebooks = [
            Notebook.from_dict(nb_data) for nb_data in data["subnotebooks"]
        ]
        # 🆕 Load custom path if exists - FIXED POSITION  
        if "custom_path" in data:
            notebook.custom_path = data["custom_path"]
        return notebook
    
    def get_file_note_count(self):
        count = 0
        for note in self.notes:
            if note.is_file_note:
                count += 1
        for sub_nb in self.subnotebooks:
            count += sub_nb.get_file_note_count()
        return count


class NoteManager:
    def __init__(self):
        self.notebooks_root = "notebooks_root"
        self.ensure_notebooks_root()
        self.notebooks = []
        self.git_managers = {}  # ADDED: Git managers dictionary
        self.load_all_notebooks()
    
    # 🆕 ADD THIS METHOD HERE:
    def get_registry_file(self):
        """Get the path to the registry file"""
        return os.path.join(self.notebooks_root, "notebooks_registry.json")

    def ensure_notebooks_root(self):
        if not os.path.exists(self.notebooks_root):
            os.makedirs(self.notebooks_root)

    def get_notebook_folder_path(self, notebook_name):
        """Override to handle custom locations"""
        # First check if we have a notebook with custom path
        for notebook in self.notebooks:
            if notebook.name == notebook_name and hasattr(notebook, 'custom_path'):
                return notebook.custom_path
    
        # Fallback to default location
        folder_name = notebook_name.replace(" ", "-")
        return os.path.join(self.notebooks_root, folder_name)

    def get_notebook_file_paths(self, notebook_name):
        """Return paths for all three JSON files"""
        folder_path = self.get_notebook_folder_path(notebook_name)
        structure_file = os.path.join(folder_path, "structure.json")
        notes_file = os.path.join(folder_path, "notes.json")      # 🆕
        files_file = os.path.join(folder_path, "files.json")      # 🆕
        return structure_file, notes_file, files_file

    def notebook_exists(self, notebook_name):
        """Check if notebook exists by name in registry ONLY"""
        registry_data = self.load_registry()
    
        # Check registry ONLY for existing notebook with same name
        for notebook_info in registry_data["notebooks"].values():
            if notebook_info["name"] == notebook_name:
                return True
    
        return False  # 🆕 NO FALLBACK TO FILE SYSTEM CHECK

    def save_notebook(self, notebook):
        # Only root notebooks get their own folders
        if notebook.parent_id is not None:
            # This is a subnotebook - save through its root parent
            root_notebook = self._find_root_notebook(notebook)
            if root_notebook:
                self.save_notebook(root_notebook)  # Save the entire hierarchy
            return

        # Only root notebooks reach this point
        folder_path = self.get_notebook_folder_path(notebook.name)
        os.makedirs(folder_path, exist_ok=True)

        structure_file, notes_file, files_file = self.get_notebook_file_paths(notebook.name)

        # SAVE STRUCTURE (metadata only - no content)
        structure_data = notebook.to_dict()
        with open(structure_file, "w") as f:
            json.dump(structure_data, f, indent=2)

        # 🆕 FIX: Use the correct method with THREE parameters
        notes_map = {}
        files_map = {}
        self._extract_file_content_from_notebook(notebook, notes_map, files_map)  # ✅ CORRECT

        # SAVE NOTES.JSON (internal notes only)
        with open(notes_file, "w") as f:
            json.dump(notes_map, f, indent=2)

        # SAVE FILES.JSON (file notes only)  
        with open(files_file, "w") as f:
            json.dump(files_map, f, indent=2)

    def _extract_file_content_from_notebook(self, notebook, notes_map, files_map):
        """Separate note content and file content"""
        for note in notebook.notes:
            if note.is_file_note:
                # File notes go to files.json
                files_map[note.id] = note.content
            else:
                # Regular notes go to notes.json  
                notes_map[note.id] = note.content

        for sub_nb in notebook.subnotebooks:
            self._extract_file_content_from_notebook(sub_nb, notes_map, files_map)

    def _apply_file_content_to_notebook(self, notebook, notes_map, files_map):
        """Apply separated content back to notes"""
        for note in notebook.notes:
            if note.is_file_note and note.id in files_map:
                note.content = files_map[note.id]
            elif not note.is_file_note and note.id in notes_map:
                note.content = notes_map[note.id]

        for sub_nb in notebook.subnotebooks:
            self._apply_file_content_to_notebook(sub_nb, notes_map, files_map)

    def load_notebook(self, notebook_name):
        structure_file, notes_file, files_file = self.get_notebook_file_paths(notebook_name)

        if not os.path.exists(structure_file):
            return None

        with open(structure_file, "r") as f:
            structure_data = json.load(f)

        notebook = Notebook.from_dict(structure_data)

        # 🆕 CLEAN SEPARATED LOADING
        notes_map = {}
        files_map = {}

        if os.path.exists(notes_file):
            with open(notes_file, "r") as f:
                notes_map = json.load(f)

        if os.path.exists(files_file):
            with open(files_file, "r") as f:
                files_map = json.load(f)

        self._apply_file_content_to_notebook(notebook, notes_map, files_map)  # ✅ CORRECT
        return notebook

    def load_all_notebooks(self):
        """Load notebooks from registry ONLY and clean missing entries"""
        self.notebooks = []
    
        # 🆕 LOAD FROM REGISTRY AND CLEAN MISSING NOTEBOOKS
        registry_data = self.load_registry()
        notebooks_to_remove = []
    
        # Load all notebooks from registry and track missing ones
        for notebook_id, notebook_info in registry_data["notebooks"].items():
            folder_path = notebook_info["path"]
        
            if os.path.exists(folder_path):
                try:
                    notebook = self.load_notebook_from_path(folder_path)
                    if notebook and notebook.parent_id is None:
                        self.notebooks.append(notebook)
                        print(f"Loaded notebook: {notebook.name} from {folder_path}")
                except Exception as e:
                    print(f"Error: Could not load notebook '{notebook_info['name']}': {e}")
            else:
                # 🆕 NOTEBOOK PATH MISSING - MARK FOR REMOVAL
                print(f"Removing missing notebook: {notebook_info['name']} (path: {folder_path})")
                notebooks_to_remove.append(notebook_id)
    
        # 🆕 REMOVE MISSING NOTEBOOKS FROM REGISTRY
        if notebooks_to_remove:
            for notebook_id in notebooks_to_remove:
                del registry_data["notebooks"][notebook_id]
            self.save_registry(registry_data)
            print(f"Cleaned {len(notebooks_to_remove)} missing notebooks from registry")
                        
    def load_notebook_from_path(self, folder_path):
        """Load notebook from any folder path"""
        structure_file = os.path.join(folder_path, "structure.json")
        notes_file = os.path.join(folder_path, "notes.json")  # 🆕 CHANGE
        files_file = os.path.join(folder_path, "files.json")  # 🆕 CHANGE

        if not os.path.exists(structure_file):
            return None

        with open(structure_file, "r") as f:
            structure_data = json.load(f)

        notebook = Notebook.from_dict(structure_data)

        # Set custom_path so navigation works
        if hasattr(notebook, 'custom_path') and notebook.custom_path:
            # Already has custom path from structure.json
            pass
        else:
            # Determine if this is a custom path
            default_path = self.get_notebook_folder_path(notebook.name)
            if folder_path != default_path:
                notebook.custom_path = folder_path

        # 🆕 FIX: Use the new three-file loading system
        notes_map = {}
        files_map = {}
    
        if os.path.exists(notes_file):
            with open(notes_file, "r") as f:
                notes_map = json.load(f)

        if os.path.exists(files_file):
            with open(files_file, "r") as f:
                files_map = json.load(f)

        self._apply_file_content_to_notebook(notebook, notes_map, files_map)  # ✅ CORRECT

        return notebook
    
    def save_data(self):
        for notebook in self.notebooks:
            self.save_notebook(notebook)

    def save_notebook(self, notebook):
        # Only root notebooks get their own folders
        if notebook.parent_id is not None:
            root_notebook = self._find_root_notebook(notebook)
            if root_notebook:
                self.save_notebook(root_notebook)
            return

        folder_path = self.get_notebook_folder_path(notebook.name)
        os.makedirs(folder_path, exist_ok=True)

        structure_file, notes_file, files_file = self.get_notebook_file_paths(notebook.name)

        # SAVE STRUCTURE (metadata only)
        structure_data = notebook.to_dict()
        with open(structure_file, "w") as f:
            json.dump(structure_data, f, indent=2)

        # 🆕 SEPARATE CONTENT SAVING
        notes_map = {}
        files_map = {}
        self._extract_file_content_from_notebook(notebook, notes_map, files_map)
    
        # Save notes.json (internal/vim notes only)
        with open(notes_file, "w") as f:
            json.dump(notes_map, f, indent=2)
    
        # Save files.json (file notes only)
        with open(files_file, "w") as f:
            json.dump(files_map, f, indent=2)

    def delete_notebook(self, notebook_to_delete):
        """Delete notebook using registry as single source of truth"""
        # GET PATH FROM REGISTRY BEFORE UNREGISTERING
        registry_data = self.load_registry()
        notebook_path = None
    
        if notebook_to_delete.id in registry_data["notebooks"]:
            notebook_path = registry_data["notebooks"][notebook_to_delete.id]["path"]
    
        # Remove from memory list
        for i, notebook in enumerate(self.notebooks):
            if notebook.id == notebook_to_delete.id:
                self.notebooks.pop(i)
                break
    
        # Unregister from registry (this removes the entry)
        self.unregister_notebook(notebook_to_delete.id)
    
        # DELETE FROM DISK using registry path
        if notebook_path and os.path.exists(notebook_path):
            shutil.rmtree(notebook_path)

    def find_notebook_by_id(self, notebook_id, notebooks=None):
        if notebooks is None:
            notebooks = self.notebooks

        for notebook in notebooks:
            if notebook.id == notebook_id:
                return notebook
            found = self.find_notebook_by_id(notebook_id, notebook.subnotebooks)
            if found:
                return found
        return None

    def find_note_by_id(self, notebook_id, note_id):
        """Find note by ID in the entire notebook tree"""

        def search_recursive(notebooks):
            for notebook in notebooks:
                # Check notes in current notebook
                for note in notebook.notes:
                    if note.id == note_id:
                        return note, notebook

                # Check subnotebooks recursively
                if notebook.subnotebooks:
                    found_note, found_notebook = search_recursive(notebook.subnotebooks)
                    if found_note:
                        return found_note, found_notebook
            return None, None

        # If specific notebook provided, search there first (faster)
        if notebook_id:
            notebook = self.find_notebook_by_id(notebook_id)
            if notebook:
                for note in notebook.notes:
                    if note.id == note_id:
                        return note, notebook

        # Search entire tree
        return search_recursive(self.notebooks)

    def get_notebook_hierarchy(self, notebook_id):
        def find_hierarchy(current_id, current_notebooks, current_path):
            for notebook in current_notebooks:
                if notebook.id == current_id:
                    return current_path + [notebook]
                found = find_hierarchy(
                    current_id, notebook.subnotebooks, current_path + [notebook]
                )
                if found:
                    return found
            return None

        return find_hierarchy(notebook_id, self.notebooks, [])

    def get_total_note_count(self):
        count = 0
        for notebook in self.notebooks:
            count += notebook.get_total_note_count()
        return count

    def get_total_notebook_count(self):
        count = 0
        for notebook in self.notebooks:
            count += 1 + notebook.get_total_subnotebook_count()
        return count

    def get_git_manager(self, notebook_name):
        """Get or create Git manager for notebook"""
        folder_path = self.get_notebook_folder_path(notebook_name)
        if folder_path not in self.git_managers:
            self.git_managers[folder_path] = GitManager(folder_path)
        return self.git_managers[folder_path]
    
    def create_notebook(self, name, custom_path=None):
        """Create notebook with optional custom location"""
        if self.notebook_exists(name):
            raise ValueError(f"Notebook '{name}' already exists")

        notebook = Notebook(name)
        self.notebooks.append(notebook)

        # Use custom path if provided, otherwise default
        if custom_path:
            # 🆕 Set custom_path BEFORE saving
            notebook.custom_path = custom_path
            folder_path = os.path.expanduser(custom_path)
            self._save_notebook_to_custom_location(notebook, folder_path)
        
            # 🆕 REGISTER IN REGISTRY
            self.register_notebook(notebook, folder_path)
        else:
            folder_path = self.get_notebook_folder_path(notebook.name)
            self.save_notebook(notebook)
        
            # 🆕 REGISTER IN REGISTRY  
            self.register_notebook(notebook, folder_path)

        # SMART GIT INITIALIZATION
        try:
            git_manager = self.get_git_manager(notebook.name)
            git_manager.commit_notebook_creation(notebook.id, notebook.name, 0, 0, custom_path)
        except Exception:
            pass

        return notebook
    
    def _save_notebook_to_custom_location(self, notebook, custom_path):
        """Save notebook to custom location"""
        # Expand user directory (~/ becomes /home/user/)
        custom_path = os.path.expanduser(custom_path)

        # Create custom directory if it doesn't exist
        os.makedirs(custom_path, exist_ok=True)

        structure_file = os.path.join(custom_path, "structure.json")
        notes_file = os.path.join(custom_path, "notes.json")  # 🆕 CHANGE
        files_file = os.path.join(custom_path, "files.json")  # 🆕 CHANGE

        # Save structure file
        structure_data = notebook.to_dict()
        with open(structure_file, "w") as f:
            json.dump(structure_data, f, indent=2)

        # 🆕 FIX: Use the new three-file system
        notes_map = {}
        files_map = {}
        self._extract_file_content_from_notebook(notebook, notes_map, files_map)  # ✅ CORRECT

        # Save notes.json
        with open(notes_file, "w") as f:
            json.dump(notes_map, f, indent=2)

        # Save files.json
        with open(files_file, "w") as f:
            json.dump(files_map, f, indent=2)
            
    def get_notebook_folder_path(self, notebook_name):
        """Override to handle custom locations"""
        # First check if we have a notebook with custom path
        for notebook in self.notebooks:
            if (notebook.name == notebook_name and 
                hasattr(notebook, 'custom_path') and 
                notebook.custom_path is not None):  # 🆕 ADD THIS CHECK
                return notebook.custom_path

        # Fallback to default location
        folder_name = notebook_name.replace(" ", "-")
        return os.path.join(self.notebooks_root, folder_name)
      # 🆕 ADD THESE NEW METHODS:
    
    def load_registry(self):
        """Load the notebook registry - create if doesn't exist"""
        registry_file = self.get_registry_file()
    
        # 🆕 CREATE REGISTRY FILE IF IT DOESN'T EXIST
        if not os.path.exists(registry_file):
            self.save_registry({"notebooks": {}})
            return {"notebooks": {}}
    
        try:
            with open(registry_file, 'r') as f:
                return json.load(f)
        except:
            # 🆕 IF CORRUPTED, CREATE FRESH REGISTRY
            self.save_registry({"notebooks": {}})
            return {"notebooks": {}}
    
    def save_registry(self, registry_data):
        """Save the notebook registry"""
        registry_file = self.get_registry_file()
        try:
            with open(registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")
    
    def register_notebook(self, notebook, folder_path):
        """Register a notebook in the registry"""
        registry_data = self.load_registry()
        
        registry_data["notebooks"][notebook.id] = {
            "name": notebook.name,
            "path": folder_path,
            "created": datetime.now().isoformat()
        }
        
        self.save_registry(registry_data)
    
    def unregister_notebook(self, notebook_id):
        """Remove a notebook from the registry"""
        registry_data = self.load_registry()
        
        if notebook_id in registry_data["notebooks"]:
            del registry_data["notebooks"][notebook_id]
            self.save_registry(registry_data)

    def create_subnotebook(self, parent_notebook, name):
        """Create subnotebook (NO BRANCHES)"""
        # 1. Create subnotebook object
        subnotebook = Notebook(name, parent_id=parent_notebook.id)
        parent_notebook.subnotebooks.append(subnotebook)

        # 2. Save the structure change
        root_notebook = self._find_root_notebook(parent_notebook)
        self.save_notebook(root_notebook)

        # SMART COMMIT - CREATE SUBNOTEBOOK
        try:
            git_manager = self.get_git_manager(root_notebook.name)
            git_manager.commit_subnotebook_creation(subnotebook.id, name, root_notebook.name, 0)
        except Exception:
            pass

        return subnotebook
    
    def _sanitize_branch_name(self, name):
        """Sanitize branch name to be Git-friendly"""
        import re
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", name)
        sanitized = re.sub(r"-+", "-", sanitized)
        return sanitized[:30].strip("-")

    def _find_root_notebook(self, notebook):
        """Find the root notebook for any nested notebook"""
        current = notebook
        while current.parent_id:
            current = self.find_notebook_by_id(current.parent_id)
            if not current:
                break
        return current
    
    # ADD TO NoteManager class in terminal_notes_core.py
    def notebook_exists_by_path(self, folder_path):
        """Check if path already registered"""
        registry_data = self.load_registry()
        normalized_path = self.normalize_path_for_comparison(folder_path)
    
        for notebook_info in registry_data["notebooks"].values():
            registered_path = self.normalize_path_for_comparison(notebook_info["path"])
            if registered_path == normalized_path:
                return True
        return False

    def normalize_path_for_comparison(self, path):
        """Normalize path for cross-platform comparison"""
        expanded = os.path.expanduser(path)
        absolute = os.path.abspath(expanded)
        normalized = os.path.normcase(absolute)
        return normalized
            
class SimpleNav:
    """One stack to rule them all - follows the single path"""

    def __init__(self):
        self.stack = (
            []
        )  # Format: {'screen': 'home/list/notebook/subnotebooks/note/search', 'id': None, 'page': 0}
        self.jump_history = []  # ← MAKE SURE THIS LINE IS HERE!

    def push(self, screen, nav_id=None, page=0):
        """Move deeper into the tree"""
        self.stack.append(
            {"screen": screen, "id": nav_id, "page": page}  # notebook_id or note_id
        )

    def pop(self):
        """Move up toward root"""
        if len(self.stack) > 1:
            return self.stack.pop()
        return None

    def current(self):
        """Current location in the tree"""
        return self.stack[-1] if self.stack else None

    def replace_page(self, page):
        """Stay at same tree node, just change page"""
        if self.stack:
            self.stack[-1]["page"] = page

    def clear(self):
        """Reset navigation"""
        self.stack = []

    # ADD THESE TWO METHODS FOR JUMP BACK
    def save_jump_position(self):
        """Save current position to jump history"""
        # Make sure jump_history exists
        if not hasattr(self, "jump_history"):
            self.jump_history = []  # Initialize if missing
        if self.stack:  # Only save if we have a current position
            self.jump_history.append(self.stack.copy())
            # Keep reasonable limit
            if len(self.jump_history) > 20:
                self.jump_history.pop(0)

    def jump_back(self):
        """Jump back to previous position - CONSUMES the history"""
        # Make sure jump_history exists
        if not hasattr(self, "jump_history"):
            self.jump_history = []  # Initialize if missing
        if self.jump_history:
            previous_position = self.jump_history.pop()  # This REMOVES the entry
            self.stack = previous_position
            self.replace_page(0)

            # ADDED: Return the current position for branch switching
            return self.current()
        return None
