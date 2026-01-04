#!/usr/bin/env python3
import sys

sys.dont_write_bytecode = True
import os
import subprocess
import tempfile
import shutil
import traceback
from datetime import datetime
from terminal_notes_core import Note, Notebook, NoteManager, SimpleNav
from search_system import SimpleSearch
from comprehensive_search import ComprehensiveSearch  # 🆕 ADD THIS IMPORT
from notebook_importer import NotebookImporter  # 🆕 ADD THIS
from recovery_system import RecoverySystem
import threading  # 🆕 ADD THIS IMPORT

class TerminalNotes:
    def __init__(self):
        self.manager = NoteManager()
        # SIMPLE SINGLE STACK NAVIGATION
        self.nav = SimpleNav()
        self.nav.push("home")  # Start at home
        self.importer = NotebookImporter(self.manager, self)

        self.terminal_width = self.get_terminal_width()
        self.terminal_height = 24  # ← ADD THIS LINE (default value)
        self.search_manager = SimpleSearch(self.manager, self)
        self.allowed_extensions = {
            # Web Core
            "html",
            "js",
            "css",
            "ts",
            "scss",
            "vue",
            "jsx",
            # Backend & Systems
            "py",
            "php",
            "rb",
            "java",
            "c",
            "cpp",
            "go",
            "rs",
            "pl",
            "lua",
            # Mobile & Platforms
            "swift",
            "kt",
            # DevOps & Automation
            "sh",
            "yml",
            "yaml",
            "toml",
            "ini",
            "cfg",
            # Data & APIs
            "json",
            "xml",
            "sql",
            # Documentation
            "bib",
            "tex",
            "md",
            "txt",
            "sty",
            "cls"
        }
        self.search_results = []  # Simple search storage
        self.search_query = ""
        # ADD THESE TWO LINES:
        self.export_history = []  # Store last 3 export directories
        self.export_history_limit = 3
        self.comprehensive_search = ComprehensiveSearch(self.manager, self)  # 🆕 ADD THIS LINE
        self.recovery_system = RecoverySystem(self.manager)  # Add this line

    def get_terminal_width(self):
        try:
            columns, _ = shutil.get_terminal_size()
            return max(60, columns)
        except:
            return 80

    def get_smart_header_path(self, notebook_id):
        hierarchy = self.manager.get_notebook_hierarchy(notebook_id)
        if not hierarchy:
            return "Home"

        full_path = [nb.name for nb in hierarchy]
        available_width = self.terminal_width - 4

        # Try full numbered path first
        numbered_full_path = ""
        for idx, segment in enumerate(full_path, 1):
            numbered_full_path += f"[{idx}]{segment}/"

        if len(numbered_full_path) <= available_width:
            return numbered_full_path

        # Smart truncation with RELATIVE numbering
        current_index = len(full_path) - 1
        left_index = current_index
        right_index = current_index

        while True:
            display_parts = []
            if left_index > 0:
                display_parts.append("...")

            segment_number = 1
            for i in range(left_index, right_index + 1):
                display_parts.append(f"[{segment_number}]{full_path[i]}")
                segment_number += 1

            if right_index < len(full_path) - 1:
                display_parts.append("...")

            display_string = "/".join(display_parts) + "/"

            if len(display_string) <= available_width:
                if left_index > 0:
                    new_left = left_index - 1
                    new_parts = ["..."] if new_left > 0 else []
                    new_segment_number = 1
                    for i in range(new_left, right_index + 1):
                        new_parts.append(f"[{new_segment_number}]{full_path[i]}")
                        new_segment_number += 1
                    if right_index < len(full_path) - 1:
                        new_parts.append("...")
                    new_string = "/".join(new_parts) + "/"
                    if len(new_string) <= available_width:
                        left_index = new_left
                        continue

                if right_index < len(full_path) - 1:
                    new_right = right_index + 1
                    new_parts = ["..."] if left_index > 0 else []
                    new_segment_number = 1
                    for i in range(left_index, new_right + 1):
                        new_parts.append(f"[{new_segment_number}]{full_path[i]}")
                        new_segment_number += 1
                    if new_right < len(full_path) - 1:
                        new_parts.append("...")
                    new_string = "/".join(new_parts) + "/"
                    if len(new_string) <= available_width:
                        right_index = new_right
                        continue
                break
            else:
                if left_index < current_index:
                    left_index += 1
                elif right_index > current_index:
                    right_index -= 1
                else:
                    break

        display_parts = []
        if left_index > 0:
            display_parts.append("...")

        segment_number = 1
        for i in range(left_index, right_index + 1):
            display_parts.append(f"[{segment_number}]{full_path[i]}")
            segment_number += 1

        if right_index < len(full_path) - 1:
            display_parts.append("...")

        final_path = "/".join(display_parts) + "/"
        return final_path

    def get_numbered_path_info(self, notebook_id):
        hierarchy = self.manager.get_notebook_hierarchy(notebook_id)
        if not hierarchy:
            return {}

        full_path = [nb for nb in hierarchy]
        available_width = self.terminal_width - 4

        current_index = len(full_path) - 1
        left_index = current_index
        right_index = current_index

        while True:
            display_parts = []
            if left_index > 0:
                display_parts.append("...")

            segment_number = 1
            for i in range(left_index, right_index + 1):
                display_parts.append(f"[{segment_number}]{full_path[i].name}")
                segment_number += 1

            if right_index < len(full_path) - 1:
                display_parts.append("...")

            display_string = "/".join(display_parts) + "/"

            if len(display_string) <= available_width:
                if left_index > 0:
                    new_left = left_index - 1
                    new_parts = ["..."] if new_left > 0 else []
                    new_segment_number = 1
                    for i in range(new_left, right_index + 1):
                        new_parts.append(f"[{new_segment_number}]{full_path[i].name}")
                        new_segment_number += 1
                    if right_index < len(full_path) - 1:
                        new_parts.append("...")
                    new_string = "/".join(new_parts) + "/"
                    if len(new_string) <= available_width:
                        left_index = new_left
                        continue

                if right_index < len(full_path) - 1:
                    new_right = right_index + 1
                    new_parts = ["..."] if left_index > 0 else []
                    new_segment_number = 1
                    for i in range(left_index, new_right + 1):
                        new_parts.append(f"[{new_segment_number}]{full_path[i].name}")
                        new_segment_number += 1
                    if new_right < len(full_path) - 1:
                        new_parts.append("...")
                    new_string = "/".join(new_parts) + "/"
                    if len(new_string) <= available_width:
                        right_index = new_right
                        continue
                break
            else:
                if left_index < current_index:
                    left_index += 1
                elif right_index > current_index:
                    right_index -= 1
                else:
                    break

        number_map = {}
        display_number = 1
        for i in range(left_index, right_index + 1):
            number_map[display_number] = full_path[i]
            display_number += 1

        return number_map

    def update_terminal_size(self):
        try:
            columns, rows = shutil.get_terminal_size()
            self.terminal_width = max(60, columns)
            self.terminal_height = rows  # ← ADD THIS LINE
            return columns, rows  # ← ADD THIS LINE
        except:
            self.terminal_width = 80
            self.terminal_height = 24
            return 80, 24

    def clear_screen(self):
        os.system("clear")

    def print_header(self, title):
        self.update_terminal_size()
        separator = "=" * self.terminal_width
        print(separator)
        print(f"{title:^{self.terminal_width}}")
        print(separator)
        print()

    def print_footer(self, options):
        print()
        print("-" * self.terminal_width)
        print(options)
        print()

    def wrap_text(self, text, width=None):
        if width is None:
            width = self.terminal_width - 4

        lines = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue
            words = paragraph.split()
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) + len(current_line) <= width:
                    current_line.append(word)
                    current_length += len(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)

            if current_line:
                lines.append(" ".join(current_line))

        return lines

    def get_input(self, prompt):
        try:
            return input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ""

    def get_dynamic_page_size(self):
        try:
            _, terminal_height = shutil.get_terminal_size()
            available_lines = terminal_height - 10
            return max(5, min(20, available_lines))
        except:
            return 20

    def get_paginated_items(self, items, page=0):
        items_per_page = self.get_dynamic_page_size()
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        total_pages = (len(items) + items_per_page - 1) // items_per_page

        paginated_items = items[start_idx:end_idx]
        return paginated_items, total_pages, page + 1, items_per_page

    def get_paginated_content(self, content, page=0, lines_per_page=None):
        """Get paginated content with optional custom page size"""
        wrapped_lines = self.wrap_text(content)
    
        # 🆕 USE PROVIDED PAGE SIZE OR DEFAULT
        if lines_per_page is None:
            lines_per_page = self.get_dynamic_page_size()
    
        start_idx = page * lines_per_page
        end_idx = start_idx + lines_per_page
        total_pages = (len(wrapped_lines) + lines_per_page - 1) // lines_per_page

        paginated_lines = wrapped_lines[start_idx:end_idx]
        return paginated_lines, total_pages, page + 1, lines_per_page

    def internal_editor(self, initial_content=""):
        self.clear_screen()    
        print("Enter your note. Press Ctrl+D on empty line when finished:")
        print("-" * (self.terminal_width // 2))
        if initial_content:
            print("Current content (append below):")
            wrapped_content = self.wrap_text(initial_content, self.terminal_width - 4)
            for line in wrapped_content:
                print(f"  {line}")
            print("-" * (self.terminal_width // 2))
        print("> ", end="")

        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        if initial_content and lines:
            return initial_content + "\n" + "\n".join(lines)
        elif initial_content:
            return initial_content
        else:
            return "\n".join(lines)

    def external_editor(self, initial_content="", read_only=False, file_extension=None):
        print("🔴 USING OLD external_editor - /tmp path!")
        print("PAUSED - Press Enter to continue...")
        input()  # 🆕 THIS WILL HALT EXECUTION
        # Use the actual file extension for syntax highlighting
        suffix = f".{file_extension}" if file_extension else ".txt"
    
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            if initial_content:
                f.write(initial_content)
            f.flush()
            temp_path = f.name

        try:
            if read_only:
                editors = ["nvim -R", "vim -R", "view", "less", "more"]
                for editor in editors:
                    try:
                        editor_name = editor.split()[0]
                        if (
                            subprocess.run(
                                f"command -v {editor_name}",
                                shell=True,
                                capture_output=True,
                            ).returncode
                            == 0
                        ):
                            subprocess.run(f"{editor} {temp_path}", shell=True)
                            break
                    except:
                        continue
            else:
                editors = ["nvim", "vim", "nano"]
                for editor in editors:
                    try:
                        if (
                            subprocess.run(
                                f"command -v {editor}", shell=True, capture_output=True
                            ).returncode
                            == 0
                        ):
                            subprocess.run(f"{editor} {temp_path}", shell=True)
                            break
                    except:
                        continue

            with open(temp_path, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _perform_search(self, query):  # old search
        results = []

        def search_in_notebook(notebook):
            for note in notebook.notes:
                if (
                    query.lower() in note.title.lower()
                    or query.lower() in note.content.lower()
                ):
                    results.append((note.id, notebook.id))

            for sub_nb in notebook.subnotebooks:
                search_in_notebook(sub_nb)

        for notebook in self.manager.notebooks:
            search_in_notebook(notebook)

        return results

    # UPDATED: Better jump detection
    def should_show_jump(self):
        current = self.nav.current()
        if current and current["id"]:
            notebook_id = current["id"]
            number_map = self.get_numbered_path_info(notebook_id)

            # EXISTING: Show jump when there are multiple levels in hierarchy
            if len(number_map) > 1:
                return True

            # NEW: Show jump in root notebook view when there's jump history
            if (
                current["screen"] == "notebook"
                and hasattr(self.nav, "jump_history")
                and self.nav.jump_history
            ):
                return True

        return False

    def process_command(self, command):
        cmd = command.lower().strip()
        current = self.nav.current()

        if not current:
            return "exit"

        # Handle BACK command - SIMPLE ONE-STACK VERSION
        if cmd == "b":
            if len(self.nav.stack) > 1:
                self.nav.pop()
                return "navigate"
            else:
                return "exit"

        # Helper function to check jump history
        def has_jump_history():
            return (
                hasattr(self.nav, "jump_history")
                and self.nav.jump_history is not None
                and len(self.nav.jump_history) > 0
            )

        # Handle JUMP BACK command (jb)
        if cmd == "jb":
            if has_jump_history():
                current_position = self.nav.jump_back()
                if current_position:
                    return "navigate"
                else:
                    print("No previous jump location to return to")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                print("No jump back history available")
                self.get_input("Press Enter to continue...")
                return "continue"

        # Handle JUMP command (J1, J2, J3, etc.)
        if len(cmd) > 1 and cmd[0] == "j":
            try:
                jump_number = int(cmd[1:])
                return self.process_jump_command(jump_number)
            except ValueError:
                print("Invalid jump format. Use: J1, J2, J3, or JB")
                self.get_input("Press Enter to continue...")
                return "continue"

        # UPDATED: Handle single letter JUMP command with context-aware prompts
        if cmd == "j":
            # Check if we're in root notebook with ONLY jump-back available
            current = self.nav.current()
            is_root_with_only_jumpback = (
                current
                and current["screen"] == "notebook"
                and hasattr(self.nav, "jump_history")
                and self.nav.jump_history
                and len(self.get_numbered_path_info(current["id"]))
                <= 1  # Only self, no other targets
            )

            # Proper jump history check
            has_jump_history = (
                hasattr(self.nav, "jump_history")
                and self.nav.jump_history is not None
                and len(self.nav.jump_history) > 0
            )

            if is_root_with_only_jumpback:
                print("Jump back to previous location:")
                prompt_text = "Enter 'b': "
            elif has_jump_history:
                # STATIC + DYNAMIC prompt
                print("Jump to position j1, j2, j3, etc or 'b' to jump back:")
                prompt_text = "Enter number or 'b': "
            else:
                # STATIC prompt only
                print("Jump to position j1, j2, j3, etc:")
                prompt_text = "Enter number: "

            choice = self.get_input(prompt_text).lower().strip()

            # Process the choice
            if choice == "b":
                if has_jump_history:
                    if self.nav.jump_back():
                        return "navigate"
                    else:
                        print("No previous jump location to return to")
                        self.get_input("Press Enter to continue...")
                        return "continue"
                else:
                    print("No jump back history available")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            elif choice.startswith("j") and len(choice) > 1:
                try:
                    jump_number = int(choice[1:])
                    return self.process_jump_command(jump_number)
                except ValueError:
                    # DYNAMIC error message
                    if has_jump_history:
                        print("Invalid command. Use: number, j1, j2, j3, or b")
                    else:
                        print("Invalid command. Use: number, j1, j2, j3")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            elif choice.isdigit():
                try:
                    jump_number = int(choice)
                    return self.process_jump_command(jump_number)
                except ValueError:
                    # DYNAMIC error message
                    if has_jump_history:
                        print("Invalid command. Use: number, j1, j2, j3, or b")
                    else:
                        print("Invalid command. Use: number, j1, j2, j3")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                # DYNAMIC error message
                if has_jump_history:
                    print("Invalid command. Use: number, j1, j2, j3, or b")
                else:
                    print("Invalid command. Use: number, j1, j2, j3")
                self.get_input("Press Enter to continue...")
                return "continue"

        # Route to appropriate command processor based on current screen
        current_screen = current["screen"]
        if current_screen == "home":
            return self.process_home_command(cmd)
        elif current_screen == "list":
            return self.process_notebook_list_command(cmd)
        elif current_screen == "notebook":
            return self.process_notebook_view_command(cmd)
        elif current_screen == "subnotebooks":
            return self.process_subnotebooks_view_command(cmd)
        elif current_screen == "note":
            return self.process_note_view_command(cmd)

        return "continue"

    def process_jump_command(self, jump_number):
        """Process jump by finding existing position OR building correct path"""
        # Save current position BEFORE jumping
        self.nav.save_jump_position()

        current = self.nav.current()
        if not current or current["screen"] not in ["notebook", "subnotebooks"]:
            print("Jump only available in notebook views")
            self.get_input("Press Enter to continue...")
            return "continue"

        notebook_id = current["id"]
        if not notebook_id:
            print("Jump only available in notebook views")
            self.get_input("Press Enter to continue...")
            return "continue"

        number_map = self.get_numbered_path_info(notebook_id)

        if not number_map:
            print("No jump targets available")
            self.get_input("Press Enter to continue...")
            return "continue"

        if jump_number not in number_map:
            valid_numbers = list(number_map.keys())
            print(f"Invalid jump number. Available: {valid_numbers}")
            self.get_input("Press Enter to continue...")
            return "continue"

        target_notebook = number_map[jump_number]

        # CHECK IF TARGET NOTEBOOK IS ALREADY IN OUR NAVIGATION STACK
        target_position = None
        for i, nav_item in enumerate(self.nav.stack):
            if (
                nav_item["id"] == target_notebook.id
                and nav_item["screen"] == "notebook"
            ):
                target_position = i
                break

        if target_position is not None:
            # TARGET EXISTS IN STACK - JUST TRUNCATE TO THAT POSITION
            self.nav.stack = self.nav.stack[: target_position + 1]
            self.nav.replace_page(0)  # Reset to first page
        else:
            # TARGET NOT IN STACK - BUILD CORRECT PATH
            hierarchy = self.manager.get_notebook_hierarchy(target_notebook.id)

            if not hierarchy:
                print("Error: Could not determine notebook path")
                self.get_input("Press Enter to continue...")
                return "continue"

            # CLEAR the current navigation stack
            self.nav.clear()

            # REBUILD the navigation stack with the ACTUAL TREE PATH
            # Start with home
            self.nav.push("home")

            # Add notebook list
            self.nav.push("list", None, 0)

            # Add each notebook in the hierarchy (except the last one which is the target)
            for notebook in hierarchy[:-1]:
                self.nav.push("notebook", notebook.id, 0)

            # Finally add the target notebook
            self.nav.push("notebook", target_notebook.id, 0)

        return "navigate"

    def process_home_command(self, cmd):
        # Dynamic command processing based on notebook count
        if not self.manager.notebooks:
            # First-time user commands - MODIFIED
            if cmd == "1":
                # 🆕 REPLACE THIS LINE:
                return self.importer.show_create_or_import_screen()
            elif cmd == "2":
                return "exit"
            else:
                return "continue"
        else:
            # Regular user commands remain the same
            if cmd == "1":
                self.nav.push("list", None, 0)
                return "navigate"
            elif cmd == "2":
                self.create_notebook()
                return "continue"
            elif cmd == "3":
                return self.show_search_options()
            elif cmd == "4":
                return "exit"
            else:
                return "continue"

    def show_search_options(self):
        """Search options without Deleted Items Only"""
        while True:
            self.clear_screen()
            self.print_header("Search Notes")
    
            print("1. Quick Search (fast)")
            print("2. Comprehensive Search") 
            print("3. Back")  # 🆕 REMOVED "Deleted Items Only"
    
            print()
            self.print_footer("")
    
            choice = self.get_input("Choose [1-3]: ").strip()
    
            # 🆕 FIX: Silent filtering like home screen - only 1,2,3 work
            if choice == "1":
                result = self.search_manager.show_search_simple()
                if result == "exit":
                    return "exit"
                else:
                    continue
            elif choice == "2":
                result = self.comprehensive_search.show_search_simple()
                if result == "exit":
                    return "exit"
                elif result == "navigate":
                    return "navigate"  # 🆕 ADD: Handle navigation
                else:
                    continue
            elif choice == "3":
                return "continue"
            else:
                # 🆕 SILENTLY ignore any other input (like home screen)
                continue

    def process_notebook_list_command(self, cmd):
        current = self.nav.current()
        page = current["page"] if current else 0
        numbered_list = self.manager.notebooks
        (
            paginated_items,
            total_pages,
            current_page,
            items_per_page,
        ) = self.get_paginated_items(numbered_list, page)

        # PAGE NAVIGATION
        if cmd == "n" and current_page < total_pages:
            self.nav.replace_page(page + 1)
            return "navigate"
        elif cmd == "p" and page > 0:
            self.nav.replace_page(page - 1)
            return "navigate"

        # CREATE NOTEBOOK
        elif cmd == "c":
            self.create_notebook()
            return "navigate"

        # VIEW NOTEBOOK (supports "v" and "v#")
        elif cmd.startswith("v"):
            # Determine which notebook index to view
            if cmd == "v":
                try:
                    idx = int(self.get_input("Enter notebook number to view: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                # User typed v1, v2, etc.
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use v1, v2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            # Re-fetch current notebook list page
            current = self.nav.current()
            page = current["page"]
            numbered_list = self.manager.notebooks
            (
                paginated_items,
                total_pages,
                current_page,
                items_per_page,
            ) = self.get_paginated_items(numbered_list, page)

            # Validate and open
            if 0 <= idx < len(paginated_items):
                notebook = paginated_items[idx]
                # SIMPLE NAVIGATION: Push new location
                self.nav.push("notebook", notebook.id, 0)
                return "navigate"
            else:
                print("Invalid notebook number.")
                self.get_input("Press Enter to continue...")
                return "continue"

        # DELETE NOTEBOOK (supports d and d#)
        elif cmd.startswith("d"):
            if cmd == "d":
                try:
                    idx = int(self.get_input("Enter notebook number to delete: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use d1, d2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            # CALCULATE PAGINATION - Same as display method
            terminal_width, terminal_height = shutil.get_terminal_size()
            fixed_ui_lines = 9  # Header(4) + Page indicator(2) + Footer(3)
            available_for_items = terminal_height - fixed_ui_lines
            items_per_page = int(available_for_items * 0.9)
            items_per_page = max(1, items_per_page)

            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            paginated_items = numbered_list[start_idx:end_idx]

            if 0 <= idx < len(paginated_items):
                notebook = paginated_items[idx]
                confirm = self.get_input(f"Delete notebook '{notebook.name}'? [y/N]: ")
                if confirm.lower() == "y":
                    # CALL THE PROPER DELETE METHOD THAT DELETES FOLDERS
                    self.manager.delete_notebook(notebook)
                    print("Notebook deleted.")
                    self.nav.replace_page(0)
                    return "navigate"
                else:
                    print("Cancelled.")
            else:
                print("Invalid notebook number.")
            self.get_input("Press Enter to continue...")
            return "continue"

        # FALLBACK
        else:
            return "continue"

    def process_notebook_view_command(self, cmd):
        current = self.nav.current()
        if not current:
            return "continue"

        notebook_id = current["id"]
        page = current["page"]
        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            print("Error: Notebook not found")
            self.get_input("Press Enter to continue...")
            return "continue"

        # CALCULATE PAGINATION - Same as display method
        try:
            _, terminal_height = shutil.get_terminal_size()
            fixed_lines = 4 + 2 + 2 + 3  # Header + Notes header + Page indicator + Footer
            if notebook.subnotebooks:
                fixed_lines += 2  # Subnotebook section
            available_for_notes = terminal_height - fixed_lines
            items_per_page = int(available_for_notes * 0.9)
            items_per_page = max(1, items_per_page)
        except:
            items_per_page = 10

        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        paginated_notes = notebook.notes[start_idx:end_idx]
        total_pages = (len(notebook.notes) + items_per_page - 1) // items_per_page
        displayed_notes_count = len(paginated_notes)
        has_subnotebooks = len(notebook.subnotebooks) > 0

        # Page navigation
        if cmd == "n":
            if page < total_pages - 1:
                self.nav.replace_page(page + 1)
                return "navigate"
            else:
                print("Already on the last page.")
                self.get_input("Press Enter to continue...")
                return "continue"
        elif cmd == "p" and page > 0:
            self.nav.replace_page(page - 1)
            return "navigate"

        # CREATE
        elif cmd == "c":
            choice = self.show_create_choice_screen(notebook)
            if choice == "1":
                self.create_note(notebook)
                self.nav.replace_page(0)
                return "navigate"
            elif choice == "2":
                self.create_file_note(notebook)
                self.nav.replace_page(0)
                return "navigate"
            elif choice == "3":
                self.nav.push("subnotebooks", notebook_id, 0)
                return "navigate"
            else:
                print("Invalid choice.")
                self.get_input("Press Enter to continue...")
                return "continue"

        # VIEW: supports v and v# and sub-notebook quick view if last slot
        elif cmd.startswith("v"):
            # If plain 'v', ask for number
            if cmd == "v":
                try:
                    idx = int(self.get_input("Enter item number to view: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use v1, v2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            # If idx is equal to displayed_notes_count and subnotebooks exist -> open subnotebooks
            if idx == displayed_notes_count and has_subnotebooks:
                self.nav.push("subnotebooks", notebook_id, 0)
                return "navigate"
            # If idx within notes list -> open note
            if 0 <= idx < displayed_notes_count:
                note = paginated_notes[idx]
                self.nav.push("note", note.id, 0)
                return "navigate"
            else:
                print("Invalid item number.")
                self.get_input("Press Enter to continue...")
                return "continue"

        # DELETE (supports d and d#)
        elif cmd.startswith("d"):
            if cmd == "d":
                try:
                    idx = int(self.get_input("Enter item number to delete: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use d1, d2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            if 0 <= idx < displayed_notes_count:
                note = paginated_notes[idx]
                confirm = self.get_input(f"Delete note '{note.title}'? [y/N]: ")
                if confirm.lower() == "y":
                    notebook.notes.remove(note)
                    self.manager.save_data()

                    # SMART COMMIT - DELETE NOTE
                    try:
                        root_notebook = self.manager._find_root_notebook(notebook)
                        git_manager = self.manager.get_git_manager(root_notebook.name)
                        git_manager.commit_note_deletion(note.id, note.title, root_notebook.name, note.is_file_note)
                    except Exception:
                        pass

                    print("Note deleted.")
                    self.nav.replace_page(0)
                    return "navigate"
                else:
                    print("Deletion cancelled.")
                    return "continue"  
            else:
                print("Invalid item number.")
                self.get_input("Press Enter to continue...")
                return "continue"

        # RENAME (r or r#)
        elif cmd.startswith("r"):
            if cmd == "r":
                try:
                    idx = int(self.get_input("Enter note number to rename: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use r1, r2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            if 0 <= idx < displayed_notes_count:
                self.rename_note(paginated_notes[idx])
                self.nav.replace_page(0)
                return "navigate"
            else:
                print("Invalid note number.")
                self.get_input("Press Enter to continue...")
                return "continue"
        elif cmd == "q":
            confirm = self.get_input("Quit Terminal Notes? [y/N]: ")
            if confirm.lower() == "y":
                return "exit"
        else:
            return "continue"

    def process_subnotebooks_view_command(self, cmd):
        current = self.nav.current()
        if not current:
            return "continue"

        parent_notebook_id = current["id"]
        page = current["page"]

        parent_notebook = self.manager.find_notebook_by_id(parent_notebook_id)
        if not parent_notebook:
            print("Error: Parent notebook not found")
            self.get_input("Press Enter to continue...")
            return "continue"

        numbered_list = parent_notebook.subnotebooks
    
        # SIMPLE pagination - just get current page items
        items_per_page = 12  # Use same fixed number as display
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        paginated_items = numbered_list[start_idx:end_idx]
        total_pages = (len(numbered_list) + items_per_page - 1) // items_per_page

        # Page navigation
        if cmd == "n" and page < total_pages - 1:
            self.nav.replace_page(page + 1)
            return "navigate"
        elif cmd == "p" and page > 0:
            self.nav.replace_page(page - 1)
            return "navigate"

        # CREATE subnotebook
        elif cmd == "c":
            self.create_subnotebook(parent_notebook)
            return "navigate"

        # VIEW subnotebook (v and v#)
        elif cmd.startswith("v"):
            if not paginated_items:
                print("No subnotebooks available.")
                self.get_input("Press Enter to continue...")
                return "continue"

            if cmd == "v":
                try:
                    idx = int(self.get_input("Enter subnotebook number to view: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use v1, v2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            if 0 <= idx < len(paginated_items):
                notebook = paginated_items[idx]
                self.nav.push("notebook", notebook.id, 0)
                return "navigate"
            else:
                print("Invalid subnotebook number.")
                self.get_input("Press Enter to continue...")
                return "continue"

        # DELETE subnotebook
        elif cmd.startswith("d"):
            if cmd == "d":
                try:
                    idx = int(self.get_input("Enter subnotebook number to delete: ")) - 1
                except ValueError:
                    print("Please enter a valid number.")
                    self.get_input("Press Enter to continue...")
                    return "continue"
            else:
                try:
                    idx = int(cmd[1:]) - 1
                except ValueError:
                    print("Invalid format. Use d1, d2, etc.")
                    self.get_input("Press Enter to continue...")
                    return "continue"

            if 0 <= idx < len(paginated_items):
                notebook = paginated_items[idx]
                confirm = self.get_input(
                    f"Delete notebook '{notebook.name}' and all its contents? [y/N]: "
                )
                if confirm.lower() == "y":
                    parent_notebook.subnotebooks.remove(notebook)
                    self.manager.save_data()

                    try:
                        root_notebook = self.manager._find_root_notebook(parent_notebook)
                        git_manager = self.manager.get_git_manager(root_notebook.name)
                        git_manager.commit_subnotebook_deletion(notebook.id, notebook.name, root_notebook.name)
                    except Exception:
                        pass

                    print("Notebook deleted.")
                    # 🆕 FIX: Go to previous page if current page becomes empty
                    total_pages = (len(parent_notebook.subnotebooks) + items_per_page - 1) // items_per_page
                    current_page = page + 1
                    
                    # If we're beyond the last page after deletion, go back one page
                    if current_page > total_pages and total_pages > 0:
                        self.nav.replace_page(total_pages - 1)
                    
                    return "navigate"
                else:
                    print("Deletion cancelled.")
            else:
                print("Invalid subnotebook number.")
            self.get_input("Press Enter to continue...")
            return "continue"
    
        elif cmd == "q":
            confirm = self.get_input("Quit Terminal Notes? [y/N]: ")
            if confirm.lower() == "y":
                return "exit"
        else:
            return "continue"
        
    def process_note_view_command(self, cmd):
        current = self.nav.current()
        if not current:
            return "continue"

        note_id = current["id"]
        page = current["page"]

        # Find the note and its notebook
        note_found, notebook_found = self.manager.find_note_by_id(None, note_id)

        if not note_found or not notebook_found:
            print("Error: Note not found")
            self.get_input("Press Enter to continue...")
            return "continue"

        note = note_found
        notebook = notebook_found

        # Use the same helper method for consistent calculation
        terminal_width, terminal_height = shutil.get_terminal_size()
        pagination_info = self.calculate_note_pagination(note.content, terminal_height)
        needs_pagination = pagination_info['needs_pagination']
        total_pages = pagination_info['total_pages']

        # Page navigation
        if cmd == "p" and page > 0:
            self.nav.replace_page(page - 1)
            return "navigate"
        elif cmd == "n":
            if needs_pagination and page < total_pages - 1:
                self.nav.replace_page(page + 1)
                return "navigate"
            else:
                print("Already on the last page.")
                self.get_input("Press Enter to continue...")
                return "continue"
        elif cmd == "e":
            self.clear_screen()

            # Store original content for comparison
            original_content = note.content
            # 🆕 Use recovery-enabled external editor
            if note.is_file_note:
                new_content = self.external_editor_with_recovery(
                    note.content, 
                    file_extension=note.file_extension,
                    note_uuid=note.id,
                    parent_notebook_uuid=notebook.id,
                    note_title=note.title
                )
            else:
                new_content = self.external_editor_with_recovery(
                    note.content,
                    note_uuid=note.id,
                    parent_notebook_uuid=notebook.id,
                    note_title=note.title
                )

            if new_content is not None and new_content != original_content:
                note.content = new_content
                note.updated = datetime.now()
                self.manager.save_data()

                try:
                    root_notebook = self.manager._find_root_notebook(notebook)
                    git_manager = self.manager.get_git_manager(root_notebook.name)
                    git_manager.commit_note_edit(note.id, note.title, root_notebook.name, original_content, new_content)
                except Exception:
                    pass
            elif new_content == original_content:
                print("No changes made.")
                self.get_input("Press Enter to continue...")

            return "continue"
        elif cmd == "x" and note.is_file_note:
            self.export_file_note(note)
            return "continue"
        elif cmd == "v":
            if note.is_file_note:
                self.external_editor(note.content, read_only=True, file_extension=note.file_extension)
            else:
                self.external_editor(note.content, read_only=True)
            return "continue"
        elif cmd == "r":
            self.rename_note(note)
            return "continue"
        elif cmd == "t":
            # Use comprehensive search's timeline feature
            result = self.comprehensive_search.show_note_timeline(note.id, notebook.id)
            if result == "exit":
                return "exit"
            return "continue"
        elif cmd == "q":
            confirm = self.get_input("Quit Terminal Notes? [y/N]: ")
            if confirm.lower() == "y":
                return "exit"
        else:
            pass

        return "continue"

    def show_home_screen(self):
        self.clear_screen()
        self.print_header("TERMINAL NOTES ©")

        if not self.manager.notebooks:
            # First-time user experience
            print("1. Create or Import a notebook")
            print("2. Quit")
        else:
            # Regular user with notebooks - FIXED COUNTING
            total_notes = self.manager.get_total_note_count()  # Includes ALL notes
            root_notebooks = len(self.manager.notebooks)
            total_files = self.count_total_files()  # File notes (subset of total_notes)
        
            # Calculate actual regular notes (non-file notes)
            regular_notes = total_notes - total_files

            # Build the count string without double-counting
            count_parts = []
            if root_notebooks > 0:
                notebook_text = f"{root_notebooks} notebook{'s' if root_notebooks != 1 else ''}"
                count_parts.append(notebook_text)

            if regular_notes > 0:
                note_text = f"{regular_notes} note{'s' if regular_notes != 1 else ''}"
                count_parts.append(note_text)

            if total_files > 0:
                file_text = f"{total_files} file{'s' if total_files != 1 else ''}"
                count_parts.append(file_text)

            count_string = f" ({', '.join(count_parts)})" if count_parts else ""

            print(f"1. List Notebooks{count_string}")
            print("2. Create Notebook")
            print("3. Search Notes")
            print("4. Quit")

        print()
        self.print_footer("")

    def show_notebook_list_screen(self):
        current = self.nav.current()
        if not current:
            return

        self.clear_screen()

        page = current["page"] if current else 0

        numbered_list = self.manager.notebooks
        total_items = len(numbered_list)

        # Get terminal size
        terminal_width, terminal_height = shutil.get_terminal_size()

        # MANUAL HEADER - FIRST THING AFTER CLEAR_SCREEN
        separator = "=" * terminal_width
        print(separator)
    
        notebook_count = len(self.manager.notebooks)
        if notebook_count == 1:
            header_base = "Root Notebook"
        else:
            header_base = "Root Notebooks"

        # ADJUSTED CALCULATION - 90% instead of 80%
        fixed_ui_lines = 9  # Header(4) + Page indicator(2) + Footer(3)
        available_for_items = terminal_height - fixed_ui_lines
        items_per_page = int(available_for_items * 0.9)  # ← CHANGED TO 90%
        items_per_page = max(1, items_per_page)

        total_pages = (total_items + items_per_page - 1) // items_per_page
        current_page = page + 1

        notebook_count = len(self.manager.notebooks)
        if notebook_count == 1:
            header_base = "Root Notebook"
        else:
            header_base = "Root Notebooks"

        header_text = header_base  # No page count
                
        print(f"{header_text:^{terminal_width}}")
        print(separator)
        print()  # Empty line after header

        # Get paginated items
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        paginated_items = numbered_list[start_idx:end_idx]

        if not paginated_items:
            print("No notebooks yet.")
            print()
        else:
            # DISPLAY LIMITED ITEMS - safety check
            for i, notebook in enumerate(paginated_items, 1):
                if i > items_per_page:  # SAFETY CHECK
                    break
                
                note_count = notebook.get_total_note_count()
                sub_count = notebook.get_total_subnotebook_count()
                file_count = notebook.get_file_note_count()
                regular_note_count = note_count - file_count

                parts = []
                if regular_note_count > 0:
                    parts.append(
                        f"{regular_note_count} note{'s' if regular_note_count != 1 else ''}"
                    )
                if file_count > 0:
                    parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
                if sub_count > 0:
                    parts.append(f"{sub_count} sub{'s' if sub_count != 1 else ''}")

                count_display = f" ({', '.join(parts)})" if parts else ""
                print(f"[{i}] {notebook.name}{count_display}")

        # Page indicator with empty line after
        if total_pages > 1:
            print(f"\n--- Page {current_page} of {total_pages} ---")
            print()  # Empty line after page indicator
        else:
            print()  # ADD THIS: Empty line before footer when no pagination

        footer_options = ["[C]reate", "[B]ack"]
        if self.manager.notebooks:
            footer_options.insert(1, "[V]iew")
            footer_options.append("[D]elete")

        if total_pages > 1:
            if current_page < total_pages:
                footer_options.insert(0, "[N]ext")
            if current_page > 1:
                footer_options.insert(0, "[P]revious")

        # MANUAL FOOTER
        print("-" * terminal_width)
        print("  ".join(footer_options))
        print()  # Empty line for input

    def show_notebook_view_screen(self):
        current = self.nav.current()
        if not current:
            return

        self.clear_screen()

        notebook_id = current["id"]
        page = current["page"]  # 🆕 KEEP THIS LINE - it's needed later!

        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            print("Error: Notebook not found")
            self.get_input("Press Enter to continue...")
            return

        # 🆕 SILENT RECOVERY - Check for any unsaved work
        recovered_count = self.recovery_system.recover_notebook_content(notebook)

        # Continue with normal display...
        smart_path = self.get_smart_header_path(notebook.id)
        self.print_header(smart_path)        

        # UPDATED DYNAMIC PAGINATION - Same 90% approach
        try:
            _, terminal_height = shutil.get_terminal_size()

            # Count fixed UI elements
            fixed_lines = 4  # Header
            fixed_lines += 2  # "Notes & Files" header
            fixed_lines += 2  # Page indicator (when needed)
            fixed_lines += 3  # Footer

            if notebook.subnotebooks:
                fixed_lines += 2  # Subnotebook section (reduced from 3)

            # What's left for notes - use 90% for more items
            available_for_notes = terminal_height - fixed_lines
            items_per_page = int(available_for_notes * 0.9)  # ← CHANGED TO 90%
            items_per_page = max(1, items_per_page)

        except:
            items_per_page = 10  # Fallback
    
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        total_pages = (len(notebook.notes) + items_per_page - 1) // items_per_page
        paginated_notes = notebook.notes[start_idx:end_idx]
        notes_current_page = page + 1
        notes_total_pages = total_pages
        
        if paginated_notes:
            # 🆕 FIX: Use recursive counting for subnotebooks
            if notebook.parent_id is not None:  # This is a subnotebook
                total_notes = notebook.get_total_note_count()  # Recursive count
                total_files = notebook.get_file_note_count()   # Recursive count  
                regular_note_count = total_notes - total_files
                file_count = total_files
            else:  # Root notebook
                file_count = sum(1 for note in notebook.notes if note.is_file_note)
                regular_note_count = len(notebook.notes) - file_count

            # Surgical pluralization for header
            if regular_note_count == 1 and file_count == 0:
                header_text = "Note & File:"
            elif regular_note_count == 0 and file_count == 1:
                header_text = "Note & File:"
            else:
                header_text = "Notes & Files:"

            counter_parts = []
            if regular_note_count > 0:
                counter_parts.append(
                    f"{regular_note_count} note{'s' if regular_note_count != 1 else ''}"
                )
            if file_count > 0:
                counter_parts.append(
                    f"{file_count} file{'s' if file_count != 1 else ''}"
                )

            counter_string = f" ({', '.join(counter_parts)})" if counter_parts else ""

            print(f"{header_text}{counter_string}")
            for i, note in enumerate(paginated_notes, 1):
                updated = note.updated.strftime("%b %d %H:%M")
                # Calculate available space for title
                timestamp_text = f"[Updated: {updated}]"
                available_for_title = (
                    self.terminal_width - len(str(i)) - len(timestamp_text) - 6
                )  # Spaces and brackets

                # Truncate title if needed
                title_display = note.title
                if len(title_display) > available_for_title:
                    title_display = title_display[: available_for_title - 3] + "..."

                # Right-align the timestamp
                padding = available_for_title - len(title_display)
                print(f"[{i}] {title_display}{' ' * padding}{timestamp_text}")

            if notes_total_pages > 1:
                print(f"\n--- Page {notes_current_page} of {notes_total_pages} ---")
            print()

        if notebook.subnotebooks:
            next_number = len(paginated_notes) + 1
            sub_count = len(notebook.subnotebooks)

            # Surgical pluralization - consistent with Note & File pattern
            if sub_count == 1:
                print(f"Sub-notebook: ({sub_count} sub)")
                print(f"[{next_number}] View Sub-notebook =>")
            else:
                print(f"Sub-notebooks: ({sub_count} subs)")
                print(f"[{next_number}] View Sub-notebooks =>")
        if not paginated_notes and not notebook.subnotebooks:
            print("This notebook is empty.")
            print("Create note, file or sub-notebook to get started!")
            print()

        footer_options = ["[C]reate", "[B]ack", "[Q]uit"]
        if self.should_show_jump():
            footer_options.insert(1, "[J]ump")

        if notes_total_pages > 1:
            if notes_current_page > 1:
                footer_options.insert(0, "[P]revious")
            if notes_current_page < notes_total_pages:
                footer_options.insert(0, "[N]ext")

        if notebook.notes or notebook.subnotebooks:
            footer_options.insert(1, "[V]iew")

        if notebook.notes:
            footer_options.insert(-1, "[D]elete")

        self.print_footer("  ".join(footer_options))

    def show_subnotebooks_view_screen(self):
        current = self.nav.current()
        if not current:
            return

        parent_notebook_id = current["id"]
        page = current["page"]

        parent_notebook = self.manager.find_notebook_by_id(parent_notebook_id)
        if not parent_notebook:
            print("Error: Parent notebook not found")
            self.get_input("Press Enter to continue...")
            return

        # 🆕 MOVE RECOVERY HERE - before any screen rendering
        print("🔄 BEFORE recovery")  # 🆕 DEBUG
        recovered_count = self.recovery_system.recover_notebook_content(parent_notebook)
        print("🔄 AFTER recovery")   # 🆕 DEBUG

        # 🆕 NOW clear and render ONCE
        self.clear_screen()

        # Get terminal size for this screen
        terminal_width, terminal_height = shutil.get_terminal_size()

        # HEADER - 4 LINES (with empty line after)
        separator = "=" * terminal_width
        print(separator)
        smart_path = self.get_smart_header_path(parent_notebook.id)
        header_title = f"{smart_path} =>"
        print(f"{header_title:^{terminal_width}}")
        print(separator)
        print()  # ADDED: Empty line after header

        numbered_list = parent_notebook.subnotebooks
        total_items = len(numbered_list)

        # ADJUSTED CALCULATION - account for the added empty line
        fixed_ui_lines = 8  # Header(4) + Title(1) + Page indicator(1) + Footer(2)
        available_for_items = terminal_height - fixed_ui_lines
    
        items_per_page = int(available_for_items * 0.8)
        items_per_page = max(1, items_per_page)

        total_pages = (total_items + items_per_page - 1) // items_per_page
        needs_pagination = total_pages > 1

        # Get paginated items for current page
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        paginated_items = numbered_list[start_idx:end_idx]
        current_page = page + 1

        if not paginated_items:
            print("No subnotebooks yet.")
            print()
        else:
            total_sub_count = len(parent_notebook.subnotebooks)
            parent_name = parent_notebook.name

            notebook_plural = "Sub-notebook" if total_sub_count == 1 else "Sub-notebooks"
            count_plural = "sub" if total_sub_count == 1 else "subs"
            count_display = f"{total_sub_count} {count_plural}"

            print(f"{notebook_plural} of '{parent_name}' ({count_display}):")

            # Display items
            for i, notebook in enumerate(paginated_items, 1):
                if i > items_per_page:  # Safety check
                    break
                note_count = notebook.get_total_note_count()
                sub_count = notebook.get_total_subnotebook_count()
                file_count = sum(1 for note in notebook.notes if note.is_file_note)
                regular_note_count = note_count - file_count

                parts = []
                if regular_note_count > 0:
                    parts.append(f"{regular_note_count} note{'s' if regular_note_count != 1 else ''}")
                if file_count > 0:
                    parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
                if sub_count > 0:
                    parts.append(f"{sub_count} sub{'s' if sub_count != 1 else ''}")

                count_display = f" ({', '.join(parts)})" if parts else ""
                print(f"[{i}] {notebook.name}{count_display}")

        # Page indicator with empty line after
        if needs_pagination:
            print(f"\n--- Page {current_page} of {total_pages} ---")
            print()  # Empty line after page indicator
        else:
            print()  # 🆕 ADD EMPTY LINE WHEN NO PAGINATION

        footer_options = ["[C]reate", "[B]ack", "[Q]uit"]

        if parent_notebook.subnotebooks:
            footer_options.insert(1, "[V]iew")
            if self.should_show_jump():
                footer_options.insert(2, "[J]ump")
            footer_options.insert(-1, "[D]elete")

        if needs_pagination:
            if current_page > 1:
                footer_options.insert(0, "[P]revious")
            if current_page < total_pages:
                footer_options.insert(0, "[N]ext")

        # Footer
        print("-" * terminal_width)
        print("  ".join(footer_options))
        print()  # Empty line for input
        
    def calculate_note_pagination(self, note_content, terminal_height):
        """Calculate pagination for note view - used by both display and command processing"""
        # Fixed lines: Header(4) + NoteInfo(2) + Separator(1) + Footer(4) = 11
        fixed_lines = 11
        available_content_lines = terminal_height - fixed_lines
        available_content_lines = max(1, available_content_lines)
    
        wrapped_lines = self.wrap_text(note_content)
        needs_pagination = len(wrapped_lines) > available_content_lines
    
        if needs_pagination:
            total_pages = (len(wrapped_lines) + available_content_lines - 1) // available_content_lines
        else:
            total_pages = 1
        
        return {
            'wrapped_lines': wrapped_lines,
            'available_content_lines': available_content_lines,
            'needs_pagination': needs_pagination,
            'total_pages': total_pages
        }

    def show_note_view_screen(self):
        current = self.nav.current()
        if not current:
            return

        # Get terminal size ONCE and use it consistently
        terminal_width, terminal_height = shutil.get_terminal_size()
        self.clear_screen()

        note_id = current["id"]
        page = current["page"]

        # Find the note
        note_found, notebook_found = self.manager.find_note_by_id(None, note_id)
        if not note_found or not notebook_found:
            print("Error: Note not found")
            self.get_input("Press Enter to continue...")
            return

        note = note_found
        notebook = notebook_found

        # HEADER - 3 LINES (no empty line after)
        separator = "=" * terminal_width
        print(separator)
        smart_path = self.get_smart_header_path(notebook.id)
        print(f"{smart_path:^{terminal_width}}")
        print(separator)
        # REMOVED: print()  # No empty line after header

        # NOTE INFO - 2 LINES
        if note.is_file_note:
            print(f"File Name: {note.title} [.{note.file_extension} file]")
        else:
            print(f"Note Title: {note.title}")
    
        timestamp = note.updated.strftime("%b %d %H:%M")
        created = note.created.strftime("%b %d")
        print(f"Created: {created}  Updated: {timestamp}")

        # SEPARATOR - 1 LINE
        print("-" * terminal_width)

        # Use the helper method for consistent calculation
        pagination_info = self.calculate_note_pagination(note.content, terminal_height)
        wrapped_lines = pagination_info['wrapped_lines']
        available_content_lines = pagination_info['available_content_lines']
        needs_pagination = pagination_info['needs_pagination']
        total_pages = pagination_info['total_pages']

        # FIXED: Use same 90% calculation as other views
        max_content_lines = int(available_content_lines * 0.9)  # ← CHANGED TO 90%
        max_content_lines = max(1, max_content_lines)

        if needs_pagination:
            # Ensure we don't go beyond the last page
            if page >= total_pages:
                page = total_pages - 1
                self.nav.replace_page(page)
        
            start_idx = page * max_content_lines
            end_idx = start_idx + max_content_lines
            paginated_lines = wrapped_lines[start_idx:end_idx]
            current_page = page + 1
        else:
            # If content fits on one page, always show page 0
            if page > 0:
                page = 0
                self.nav.replace_page(0)
            paginated_lines = wrapped_lines
            current_page = 1
            total_pages = 1

        # Display content lines - LIMITED to ensure header stays visible
        for i, line in enumerate(paginated_lines):
            if i >= max_content_lines:
                break
            print(line)

        # PAGE INDICATOR - 2 LINES (with empty line after)
        if needs_pagination:
            print(f"--- Page {current_page} of {total_pages} ---")
            print()  # Empty line after page indicator

        # FOOTER - 3 LINES
        print("-" * terminal_width)
    
        footer_options = ["[E]dit", "[V]iew", "[T]imeline", "[B]ack", "[Q]uit"]
        if self.should_show_jump():
            footer_options.insert(2, "[J]ump")
        if note.is_file_note:
            footer_options.insert(2, "[X]port")
        footer_options.insert(-1, "[R]ename")

        if needs_pagination:
            if current_page > 1:
                footer_options.insert(0, "[P]revious")
            if current_page < total_pages:
                footer_options.insert(0, "[N]ext")

        print("  ".join(footer_options))
        print()  # Empty line for input
        
    def external_editor_with_recovery(self, initial_content="", read_only=False, 
                                     file_extension=None, note_uuid=None, 
                                     parent_notebook_uuid=None, note_title=""):
        """Enhanced external editor with autosave and recovery"""
    
        # Use temp file for editing
        suffix = f".{file_extension}" if file_extension else ".txt"
        with tempfile.NamedTemporaryFile(mode="w+", suffix=suffix, delete=False, encoding="utf-8") as f:
            if initial_content:
                f.write(initial_content)
            f.flush()
            temp_path = f.name

        # 🆕 START AUTOSAVE THREAD FOR RECOVERY
        autosave_thread = None
        if not read_only and note_uuid:
            autosave_thread = threading.Thread(
                target=self._simple_autosave_loop,
                args=(temp_path, note_uuid, parent_notebook_uuid, note_title, bool(file_extension), file_extension),
                daemon=True
            )
            autosave_thread.start()

        # NEOVIM AUTOSAVE CONFIGURATION
        nvim_autosave_commands = [
            "set autowriteall",
            "set updatetime=30000",
            "autocmd CursorHold * silent! write",
            "autocmd CursorHoldI * silent! write", 
            "autocmd FocusLost * silent! write",
            "echo 'NeoVim autosave enabled - saving every 30 seconds'"
        ]

        try:
            editors = ["nvim", "vim", "nano"] if not read_only else ["nvim -R", "vim -R", "view"]
            used_editor = None
            for editor in editors:
                try:
                    editor_name = editor.split()[0]
                    if subprocess.run(f"command -v {editor_name}", shell=True, capture_output=True).returncode == 0:
                        used_editor = editor
                    
                        if editor == "nvim" and not read_only:
                            cmd_string = " -c \"" + "\" -c \"".join(nvim_autosave_commands) + "\""
                            subprocess.run(f"nvim{cmd_string} {temp_path}", shell=True)
                        else:
                            subprocess.run(f"{editor} {temp_path}", shell=True)
                        break
                except:
                    continue

            # 🆕 STOP AUTOSAVE THREAD
            if autosave_thread:
                # Thread will stop when temp file is deleted
            
                # Force one final save to recovery
                try:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        final_content = f.read()
                    self.recovery_system.save_recovery_file(
                        note_uuid, parent_notebook_uuid, final_content, note_title,
                        bool(file_extension), file_extension
                    )
                except:
                    pass

            with open(temp_path, "r", encoding="utf-8") as f:
                final_content = f.read()
            
            # 🆕 CLEAN UP RECOVERY FILE AFTER SUCCESSFUL SAVE
            if not read_only and note_uuid:
                recovery_filename = self.recovery_system.get_recovery_filename(
                    note_uuid, note_title, bool(file_extension), file_extension
                )
                recovery_path = self.recovery_system.recovery_dir / recovery_filename
                if recovery_path.exists():
                    recovery_path.unlink()
            
            return final_content
        
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _simple_autosave_loop(self, temp_path, note_uuid, parent_notebook_uuid, note_title, is_file_note, file_extension):
        """Simple autosave that copies temp file to recovery every 30 seconds"""
        import time
    
        while True:
            try:
                # Check if temp file still exists
                if not os.path.exists(temp_path):
                    break
                
                # Read current content and save to recovery
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
                self.recovery_system.save_recovery_file(
                    note_uuid, parent_notebook_uuid, content, note_title,
                    is_file_note, file_extension
                )
            
                # Wait 30 seconds
                time.sleep(30)
            
            except:
                # If any error occurs, stop the loop
                break
            
    def _start_autosave_thread(self, file_path, note_uuid, parent_notebook_uuid, 
                              note_title, is_file_note, file_extension):
        """Start background thread for autosaving to recovery"""
        import threading
        import time

        class AutosaveThread(threading.Thread):
            def __init__(self, recovery_system, file_path, note_uuid, parent_notebook_uuid,
                        note_title, is_file_note, file_extension):
                super().__init__(daemon=True)
                self.recovery_system = recovery_system
                self.file_path = file_path
                self.note_uuid = note_uuid
                self.parent_notebook_uuid = parent_notebook_uuid
                self.note_title = note_title
                self.is_file_note = is_file_note
                self.file_extension = file_extension
                self._stop_event = threading.Event()
                self.last_content = ""
                self._log(f"AUTOSAVE THREAD STARTED for {note_title}")
        
            def _log(self, message):
                """Log to file instead of screen"""
                with open("/tmp/terminal_notes_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()}: {message}\n")
        
            def run(self):
                self._log(f"AUTOSAVE: Monitoring {self.file_path}")
                while not self._stop_event.is_set():
                    try:
                        # Read current content from temp file
                        with open(self.file_path, 'r', encoding='utf-8') as f:
                            current_content = f.read()
                    
                        # Only save if content changed
                        if current_content != self.last_content:
                            self._log(f"AUTOSAVE: Content changed, saving recovery...")
                            success = self.recovery_system.save_recovery_file(
                                self.note_uuid, self.parent_notebook_uuid,
                                current_content, self.note_title,
                                self.is_file_note, self.file_extension
                            )
                            if success:
                                self._log("AUTOSAVE: Recovery file saved successfully")
                            else:
                                self._log("AUTOSAVE: Failed to save recovery file")
                            self.last_content = current_content
                    
                        # Wait before next autosave
                        self._log("AUTOSAVE: Waiting 30 seconds...")
                        self._stop_event.wait(30)
                    
                    except Exception as e:
                        self._log(f"AUTOSAVE ERROR: {e}")
                        # If we can't read the file, editor might be closed
                        break
        
            def stop(self):
                self._log("AUTOSAVE THREAD STOPPED")
                self._stop_event.set()

        thread = AutosaveThread(
            self.recovery_system, file_path, note_uuid, parent_notebook_uuid,
            note_title, is_file_note, file_extension
        )
        thread.start()
        return thread
            
    def create_note(self, notebook):
        self.clear_screen()
        self.print_header("Create New Note")

        title = self.get_input("Note title: ")
        if not title:
            return

        # 🆕 FIX: Ensure title is a single line
        # Remove any newlines that might have been accidentally entered
        title = title.replace('\n', ' ').replace('\r', ' ').strip()
    
        # If title is empty after cleaning, cancel
        if not title:
            print("Error: Title cannot be empty")
            self.get_input("Press Enter to continue...")
            return

        print()
        print("Choose editor (this choice is permanent):")
        print("1. Internal editor (quick) - Ctrl+D to save")
        print("2. Vim editor (full featured) - 'i' to write & ':wq' to save")
        choice = self.get_input("Choose [1-2]: ")

        if choice == "1":
            self.clear_screen()
            content = self.internal_editor()
        
            note = Note(title, content, created_with="internal")
            notebook.notes.append(note)
            self.manager.save_data()            

            # SMART COMMIT - DELETE NOTE
            try:
                root_notebook = self.manager._find_root_notebook(notebook)
                git_manager = self.manager.get_git_manager(root_notebook.name)
                git_manager.commit_note_deletion(note.title, root_notebook.name, note.is_file_note)
            except Exception:
                pass

        elif choice == "2":
            self.clear_screen()
            print("Opening Vim editor...")
            # 🆕 PASTE RECOVERY CODE HERE - Create note object FIRST
            note = Note(title, "", created_with="vim")  # Empty content initially

            # 🆕 Use recovery-enabled external editor
            content = self.external_editor_with_recovery(
                initial_content="",
                read_only=False,
                file_extension=None,
                note_uuid=note.id,
                parent_notebook_uuid=notebook.id,
                note_title=title
            )

            # 🆕 KEEP YOUR EXISTING VALIDATION LOGIC
            if not content or not content.strip():
                print("Note creation cancelled - no content provided.")
                self.get_input("Press Enter to continue...")
                return "continue"

            # 🆕 UPDATE THE NOTE WITH ACTUAL CONTENT
            note.content = content.strip()
            notebook.notes.append(note)
            self.manager.save_data()
            
            # SMART COMMIT - CREATE NOTE
            try:
                root_notebook = self.manager._find_root_notebook(notebook)
                git_manager = self.manager.get_git_manager(root_notebook.name)
                git_manager.commit_note_creation(note.id, title, root_notebook.name, note.created_with, content)
            except Exception:
                pass

        self.nav.replace_page(0)
        return "navigate"
    
    def rename_note(self, note):
        self.clear_screen()
        self.print_header(f"Rename Note")

        old_title = note.title
        print(f"Current name: {note.title}")

        if note.is_file_note:
            current_name = note.title
            if "." in current_name:
                name_parts = current_name.rsplit(".", 1)
                current_filename = name_parts[0]
                current_extension = name_parts[1]
                print(f"File extension: .{current_extension} (will be kept)")
                new_filename = self.get_input("New filename (without extension): ")

                if new_filename and new_filename.strip():
                    new_title = f"{new_filename.strip()}.{current_extension}"
                    note.title = new_title
                    note.updated = datetime.now()
                    self.manager.save_data()

                    # 🆕 FIX: Use consistent structured commit
                    _, notebook = self.manager.find_note_by_id(None, note.id)
                    if notebook:
                        try:
                            root_notebook = self.manager._find_root_notebook(notebook)
                            git_manager = self.manager.get_git_manager(root_notebook.name)
                            git_manager.commit_note_rename(note.id, old_title, new_title, root_notebook.name, note.is_file_note)
                        except Exception:
                            pass

                    print(f"Renamed to: {new_title}")
                else:
                    print("Filename cannot be empty.")
            else:
                new_title = self.get_input("New name: ")
                if new_title and new_title.strip():
                    note.title = new_title.strip()
                    note.updated = datetime.now()
                    self.manager.save_data()

                    # 🆕 FIX: Use consistent structured commit
                    _, notebook = self.manager.find_note_by_id(None, note.id)
                    if notebook:
                        try:
                            root_notebook = self.manager._find_root_notebook(notebook)
                            git_manager = self.manager.get_git_manager(root_notebook.name)
                            git_manager.commit_note_rename(note.id, old_title, new_title, root_notebook.name, note.is_file_note)
                        except Exception:
                            pass

                    print("Note renamed!")
                else:
                    print("Name cannot be empty.")
        else:
            new_title = self.get_input("New title: ")
            if new_title and new_title.strip():
                note.title = new_title.strip()
                note.updated = datetime.now()
                self.manager.save_data()

                # 🆕 FIX: Use consistent structured commit
                _, notebook = self.manager.find_note_by_id(None, note.id)
                if notebook:
                    try:
                        root_notebook = self.manager._find_root_notebook(notebook)
                        git_manager = self.manager.get_git_manager(root_notebook.name)
                        git_manager.commit_note_rename(note.id, old_title, new_title, root_notebook.name, note.is_file_note)
                    except Exception:
                        pass

                print("Note renamed!")
            else:
                print("Title cannot be empty.")

        self.get_input("Press Enter to continue...")
    
    def create_notebook(self):
        self.clear_screen()
        self.print_header("Create Notebook")

        name = self.get_input("Notebook name: ")
        if not name:
            return

        print()
        print("Choose notebook location:")
        print("1. Default location (notebooks_root/)")
        print("2. Custom location (any folder on your system)")
        choice = self.get_input("Choose [1-2]: ")

        # ADD VALIDATION FOR EMPTY/INVALID CHOICE
        if not choice or choice not in ["1", "2"]:
            print("Operation cancelled.")
            self.get_input("Press Enter to continue...")
            return

        custom_path = None
        if choice == "2":
            print("\nEnter full path for notebook folder:")
            print("Examples:")
            print("  /home/username/projects/notes/")
            print("  ~/Documents/work-notes/")
            print("  /tmp/temporary-notes/")
            print()
            custom_path = self.get_input("Custom path: ")
            if not custom_path.strip():
                print("Invalid path, operation cancelled.")
                self.get_input("Press Enter to continue...")
                return

        try:
            notebook = self.manager.create_notebook(name, custom_path)
            if custom_path:
                print(f"Notebook '{name}' created successfully at: {custom_path}")
            else:
                print(f"Notebook '{name}' created successfully in default location!")
            self.get_input("Press Enter to continue...")
            self.nav.replace_page(0)
        except ValueError as e:
            print(f"Error: {e}")
            self.get_input("Press Enter to continue...")

    def show_create_choice_screen(self, notebook):
        self.clear_screen()
        self.print_header(f"Create in: {notebook.name}")

        print("Choose what to create:")
        print("1 - Regular Note (internal/vim editor)")
        print("2 - Specialized File (.py, .html, .sh, etc.)")
        print("3 - Sub-notebook (nested container)")
        print()

        return self.get_input("Choose [1-3]: ")

    def create_file_note(self, notebook):
        while True:
            self.clear_screen()
            self.print_header(f"Create Specialized File in: {notebook.name}")

            print("Allowed extensions: " + ", ".join(sorted(self.allowed_extensions)[:10]) + "...")
            print()

            filename = self.get_input("File name (with extension) [blank to cancel]: ")
            if not filename.strip():
                return

            if "." not in filename:
                print("Error: File must have an extension (e.g., '.py', '.html')")
                self.get_input("Press Enter to try again...")
                continue

            extension = filename.split(".")[-1].lower()
            if extension not in self.allowed_extensions:
                print(f"Error: Extension '.{extension}' not allowed")
                self.get_input("Press Enter to try again...")
                continue

            # 🆕 PASTE RECOVERY CODE HERE - after validation, before editor
            # Create the file note with initial content that includes file-type hints
            initial_content = self.get_initial_content_for_extension(extension)
        
            # 🆕 Create file note object with UUID for recovery
            note = Note(filename, "", created_with="vim")
            note.file_extension = extension
        
            print(f"\nOpening external editor for '{filename}'...")
        
            # 🆕 Use recovery-enabled external editor
            content = self.external_editor_with_recovery(
                initial_content=initial_content,
                read_only=False,
                file_extension=extension,
                note_uuid=note.id,
                parent_notebook_uuid=notebook.id,
                note_title=filename
            )
        
            # 🆕 KEEP YOUR EXISTING VALIDATION LOGIC
            if content is not None and content.strip() and content != initial_content:
                note.content = content.strip()
                notebook.notes.append(note)
                self.manager.save_data()

                # SMART COMMIT - CREATE FILE NOTE
                try:
                    root_notebook = self.manager._find_root_notebook(notebook)
                    git_manager = self.manager.get_git_manager(root_notebook.name)
                    git_manager.commit_file_creation(note.id, filename, root_notebook.name, extension, content)
                except Exception:
                    pass

                print(f"File '{filename}' created successfully!")
            elif content == initial_content:
                print("File creation cancelled - no content added.")
            elif content is not None and not content.strip():
                print("File creation cancelled - empty content.")
            else:
                print("File creation cancelled.")
            self.get_input("Press Enter to continue...")
            break
        
    def get_initial_content_for_extension(self, extension):
        """Provide initial content hints based on file type"""
        hints = {
            # Web Core
            "html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>",
            "js": "// JavaScript file\n\n",
            "css": "/* CSS file */\n\n",
            "ts": "// TypeScript file\n\n",
            "scss": "// SCSS file\n\n",
            "vue": "<template>\n  <div>\n    \n  </div>\n</template>\n\n<script>\nexport default {\n  \n}\n</script>\n\n<style>\n\n</style>",
            "jsx": "import React from 'react';\n\nconst Component = () => {\n  return (\n    <div>\n      \n    </div>\n  );\n};\n\nexport default Component;",
        
            # Backend & Systems
            "py": "# Python file\n\n",
            "php": "<?php\n\n",
            "rb": "# Ruby file\n\n",
            "java": "// Java file\n\n",
            "c": "// C file\n\n",
            "cpp": "// C++ file\n\n",
            "go": "// Go file\n\npackage main\n\nfunc main() {\n    \n}",
            "rs": "// Rust file\n\nfn main() {\n    \n}",
            "pl": "# Perl file\n\n",
            "lua": "-- Lua file\n\n",
        
            # Mobile & Platforms
            "swift": "// Swift file\n\n",
            "kt": "// Kotlin file\n\n",
        
            # DevOps & Automation
            "sh": "#!/bin/bash\n\n",
            "yml": "---\n# YAML file\n",
            "yaml": "---\n# YAML file\n",
            "toml": "# TOML file\n\n",
            "ini": "; INI file\n\n",
            "cfg": "# Config file\n\n",
        
            # Data & APIs
            "json": "{\n  \n}",
            "xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\n",
            "sql": "-- SQL file\n\n",
        
            # Documentation
            "bib": "@article{,\n  \n}",
            "tex": "\\documentclass{article}\n\\begin{document}\n\n\n\\end{document}",
            "md": "# Markdown file\n\n",
            "txt": "",
            "sty": "\\NeedsTeXFormat{LaTeX2e}\n\\ProvidesPackage{}\n\n",
            "cls": "\\NeedsTeXFormat{LaTeX2e}\n\\ProvidesClass{}\n\n"
        }
        return hints.get(extension, "")
    
    def create_subnotebook(self, parent_notebook):
        self.clear_screen()
        self.print_header(f"Create Sub-notebook in: {parent_notebook.name}")

        name = self.get_input("Sub-notebook name: ")
        if not name:
            return

        # Use the Git-integrated method from NoteManager
        subnotebook = self.manager.create_subnotebook(parent_notebook, name)

        print(f"Sub-notebook '{name}' created successfully!")
        self.get_input("Press Enter to continue...")

    def count_total_files(self):
        """Count total file notes across all notebooks"""
        file_count = 0

        def count_files_in_notebook(notebook):
            nonlocal file_count
            for note in notebook.notes:
                if note.is_file_note:
                    file_count += 1
            for sub_nb in notebook.subnotebooks:
                count_files_in_notebook(sub_nb)

        for notebook in self.manager.notebooks:
            count_files_in_notebook(notebook)

        return file_count

    def export_file_note(self, note):
        if not note.is_file_note:
            print("This is not a file note.")
            self.get_input("Press Enter to continue...")
            return

        while True:
            self.clear_screen()
            self.print_header(f"Export File: {note.title}")

            print("Enter export DIRECTORY (filename will be automatic):")
            print("Examples:")
            print("  /home/user/projects/")
            print("  ./exports/")
            print("  ../backup/")

            # Show export history if available
            if self.export_history:
                print("\nRecent export paths:")
                for i, path in enumerate(self.export_history, 1):
                    print(f"[{i}] {path}")
            print()

            print(f"File will be saved as: {note.title}")
            print()

            if self.export_history:
                prompt = "Enter directory or number [1-3]: "
            else:
                prompt = "Export directory: "

            export_dir = self.get_input(prompt)

            if not export_dir:
                return

            # Handle number selection from history
            if export_dir.isdigit() and self.export_history:
                idx = int(export_dir) - 1
                if 0 <= idx < len(self.export_history):
                    export_dir = self.export_history[idx]
                    print(f"Using: {export_dir}")
                else:
                    print("Invalid history number.")
                    self.get_input("Press Enter to continue...")
                    continue

            export_dir = os.path.expanduser(export_dir)
            export_path = os.path.join(export_dir, note.title)

            if os.path.exists(export_path) and os.path.isdir(export_path):
                export_path = os.path.join(export_path, note.title)

            if os.path.isdir(export_path):
                print(f"Error: '{export_path}' is a directory.")
                self.get_input("Press Enter to continue...")
                return

            if os.path.exists(export_path):
                confirm = self.get_input(
                    f"File exists. Overwrite '{note.title}'? [y/N]: "
                )
                if confirm.lower() != "y":
                    print("Export cancelled.")
                    self.get_input("Press Enter to continue...")
                    return

            try:
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(note.content)
                print(f"File exported successfully to: {export_path}")

                # Update export history
                self._update_export_history(export_dir)

            except Exception as e:
                print(f"Export failed: {e}")

            self.get_input("Press Enter to continue...")
            break

    def _update_export_history(self, export_dir):
        """Update export history with new directory"""
        # Remove if already exists (to avoid duplicates)
        if export_dir in self.export_history:
            self.export_history.remove(export_dir)

        # Add to front (most recent)
        self.export_history.insert(0, export_dir)

        # Trim to limit
        if len(self.export_history) > self.export_history_limit:
            self.export_history = self.export_history[: self.export_history_limit]
    
                                                    
    def main_loop(self):
        # Initialize terminal size tracking
        self.update_terminal_size()  # ← CALL THIS FIRST
        last_terminal_size = (self.terminal_width, self.terminal_height)

        while True:
            # Check if terminal was resized
            current_width, current_height = self.update_terminal_size()
            if (current_width, current_height) != last_terminal_size:
                last_terminal_size = (current_width, current_height)
                continue  # ← USE continue INSTEAD OF return

            current = self.nav.current()
            current_screen = current["screen"]
            if current_screen == "home":
                self.show_home_screen()
                # Dynamic prompt based on notebook count
                if not self.manager.notebooks:
                    prompt = "Choose [1-2]: "
                else:
                    prompt = "Choose [1-4]: "
            elif current_screen == "list":
                self.show_notebook_list_screen()
                prompt = "> "
            elif current_screen == "notebook":
                self.show_notebook_view_screen()
                prompt = "> "
            elif current_screen == "subnotebooks":
                self.show_subnotebooks_view_screen()
                prompt = "> "
            elif current_screen == "note":
                self.show_note_view_screen()
                prompt = "> "
            else:
                break
            command = self.get_input(prompt)
            try:
                result = self.process_command(command)
            except Exception:
                # Print full traceback so we see the crash instead of vanishing
                print("An unexpected error occurred:")
                traceback.print_exc()
                self.get_input("Press Enter to continue...")
                # return to loop
                continue
            if result == "exit":
                self.clear_screen()
                break
            elif result == "navigate":  # 🆕 ADD THIS LINE
                continue  # 🆕 ADD THIS LINE


            elif result == "navigate":
                continue     

if __name__ == "__main__":
    import traceback

    try:
        app = TerminalNotes()
        app.main_loop()
    except Exception:
        print("\n--- An unexpected error occurred ---")
        traceback.print_exc()
        input("\nPress Enter to exit...")
