#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import os
import json
import subprocess
from pathlib import Path

class NotebookImporter:
    def __init__(self, note_manager, ui_controller):
        self.manager = note_manager
        self.ui = ui_controller
    
    def show_create_or_import_screen(self):
        """OS-agnostic notebook creation/import"""
        while True:
            self.ui.clear_screen()
            self.ui.print_header("Notebook Manager")
            
            print("1. Create New Notebook")
            print("2. Import Existing Notebook") 
            print("3. Back to Home")
                      
            self.ui.print_footer("")
            
            choice = self.ui.get_input("Choose [1-3]: ").strip()
            
            if choice == "1":
                self.ui.create_notebook()  # Use existing method from UI
                return "navigate"
            elif choice == "2":
                result = self.import_notebook_flow()
                if result == "success":
                    return "navigate"
                else:
                    continue
            elif choice == "3":
                return "continue"
            else:
                continue

    def import_notebook_flow(self):
        """Cross-platform import with clear validation steps"""
        self.ui.clear_screen()
        self.ui.print_header("Import Existing Notebook")
        
        print("Enter path to Terminal Notes notebook:")
        print()
        print("Platform Examples:")
        print("  Linux/Mac: /home/user/projects/notes/")
        print("  Windows:   C:\\Users\\Name\\Documents\\notes\\")
        print("  Relative:  ./my-notebook/ or ../shared-notes/")
        print()
        
        import_path = self.ui.get_input("Notebook path: ").strip()
        if not import_path:
            return "cancelled"
        
        # Cross-platform path normalization
        import_path = self.normalize_path(import_path)
        
        print(f"\nValidating: {import_path}")
        print("─" * self.ui.terminal_width)
        
        # GENERIC VALIDATION PIPELINE
        validation_pipeline = [
            ("Path Accessibility", self.validate_path_access),
            ("File Structure", self.validate_file_structure),
            ("Git Repository", self.validate_git_repository),
            ("Data Format", self.validate_data_format),
            ("Duplicate Check", self.validate_not_duplicate)
        ]
        
        validation_result = self.run_validation_pipeline(import_path, validation_pipeline)
        
        if not validation_result["success"]:
            print(f"\n Import failed: {validation_result['message']}")
            self.ui.get_input("Press Enter to continue...")
            return "failed"
        
        # PERFORM IMPORT
        print(f"\n Importing notebook...")
        success = self.import_notebook(import_path)
        
        if success:
            print(" Notebook imported successfully!")
            self.ui.get_input("Press Enter to continue...")
            return "success"
        else:
            print(" Import failed during final step")
            self.ui.get_input("Press Enter to continue...")
            return "failed"

    def normalize_path(self, path):
        """Cross-platform path normalization"""
        expanded_path = os.path.expanduser(path)
        absolute_path = os.path.abspath(expanded_path)
        normalized_path = os.path.normpath(absolute_path)
        return normalized_path

    def run_validation_pipeline(self, path, pipeline):
        """Generic validation runner"""
        for step_name, validator in pipeline:
            print(f" {step_name}... ", end="", flush=True)
            success, message = validator(path)
            if success:
                print("Validated")
            else:
                print("validation Failed")
                return {"success": False, "message": f"{step_name}: {message}"}
        
        return {"success": True, "message": "All checks passed"}

    # VALIDATION METHODS
    def validate_path_access(self, path):
        if not os.path.exists(path):
            return False, "Path does not exist"
        
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        
        if not os.access(path, os.R_OK):
            return False, "No read permission"
        
        if not os.access(path, os.W_OK):
            return False, "No write permission"
        
        return True, ""

    def validate_file_structure(self, path):
        required_files = {
            "structure.json": "Notebook metadata",
            "notes.json": "Regular note content", 
            "files.json": "File note content"
        }
        
        missing_files = []
        for filename, description in required_files.items():
            file_path = os.path.join(path, filename)
            if not os.path.exists(file_path):
                missing_files.append(f"{filename} ({description})")
        
        if missing_files:
            return False, f"Missing: {', '.join(missing_files)}"
        
        return True, ""

    def validate_git_repository(self, path):
        git_path = os.path.join(path, ".git")
        if not os.path.exists(git_path):
            return False, "Not a Git repository"
        
        essential_git_items = ["config", "HEAD"]
        for item in essential_git_items:
            item_path = os.path.join(git_path, item)
            if not os.path.exists(item_path):
                return False, f"Git repository incomplete (missing {item})"
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=path, 
                capture_output=True, 
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, "Git repository not functional"
                
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except FileNotFoundError:
            return False, "Git not installed on system"
        except Exception as e:
            return False, f"Git check failed: {str(e)}"
        
        return True, ""

    def validate_data_format(self, path):
        try:
            structure_file = os.path.join(path, "structure.json")
            with open(structure_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            structure_checks = [
                ('id', lambda x: isinstance(x, str) and len(x) > 0),
                ('name', lambda x: isinstance(x, str) and len(x) > 0),
                ('notes', lambda x: isinstance(x, list)),
                ('subnotebooks', lambda x: isinstance(x, list))
            ]
            
            for key, validator in structure_checks:
                if key not in data:
                    return False, f"Missing required field: {key}"
                if not validator(data[key]):
                    return False, f"Invalid format for: {key}"
                    
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Data validation error: {str(e)}"

    def validate_not_duplicate(self, path):
        if self.manager.notebook_exists_by_path(path):
            return False, "Notebook already imported"
        return True, ""

    def import_notebook(self, folder_path):
        try:
            notebook = self.manager.load_notebook_from_path(folder_path)
            if not notebook:
                return False
            
            self.manager.register_notebook(notebook, folder_path)
            self.manager.notebooks.append(notebook)
            self.manager.save_data()
            
            verified = self.manager.find_notebook_by_id(notebook.id)
            return verified is not None
            
        except Exception as e:
            print(f"Import error: {e}")
            return False