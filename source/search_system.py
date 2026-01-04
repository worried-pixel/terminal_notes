#!/usr/bin/env python3
from datetime import datetime
import shutil


class SimpleSearch:
    def __init__(self, note_manager, ui_methods):
        self.manager = note_manager
        self.ui = ui_methods  # Reference to main UI methods
        self.results = []
        self.query = ""
        self.current_page = 0
        self.search_nav_stack = []  # Format: {'screen': 'results/notebook/note', 'data': {}}
    
    def search(self, query):
        """Simple search through all notebooks"""
        self.query = query
        self.results = []
        self.current_page = 0
        
        def search_recursive(notebook):
            for note in notebook.notes:
                if (query.lower() in note.title.lower() or 
                    query.lower() in note.content.lower()):
                    self.results.append((note.id, notebook.id))
            for sub_nb in notebook.subnotebooks:
                search_recursive(sub_nb)
        
        for notebook in self.manager.notebooks:
            search_recursive(notebook)
        
        return self.results
    
    def handle_search_note_view(self, note_id, notebook_id, main_app):
        """Completely isolated note view within search context"""
        note, notebook = self.manager.find_note_by_id(notebook_id, note_id)
        if not note or not notebook:
            return "back"

        while True:
            self.ui.clear_screen()
    
            # SIMPLE HEADER - No jump features
            notebook_path = self.manager.get_notebook_hierarchy(notebook.id)
            if notebook_path:
                path_parts = [nb.name for nb in notebook_path]
                path_str = "/".join(path_parts) + "/"
            else:
                path_str = notebook.name           
            self.ui.print_header(f"Search: {path_str}")
    
            # Display note
            if note.is_file_note:
                print(f"File: {note.title} [.{note.file_extension}]")
            else:
                print(f"Note: {note.title}")
        
            timestamp = note.updated.strftime("%b %d %H:%M")
            print(f"Updated: {timestamp}")
            print()
    
            # Limited content preview
            content_lines = self.ui.wrap_text(note.content)
            for line in content_lines[:10]:
                print(line)
            if len(content_lines) > 10:
                print("\n... (use [V]iew for complete note)")
            print()
    
            # SEARCH-SPECIFIC FOOTER
            footer_options = ["[E]dit", "[V]iew", "[B]ack"]
            if note.is_file_note:
                footer_options.insert(2, "[X]port")
            footer_options.insert(-1, "[R]ename")
    
            self.ui.print_footer("  ".join(footer_options))
    
            cmd = self.ui.get_input("> ").strip().lower()
    
            if cmd == "b":
                return "back"
            elif cmd == "v":
                # For file notes, pass extension for syntax highlighting in read-only mode
                if note.is_file_note:
                    self.ui.external_editor(note.content, read_only=True, file_extension=note.file_extension)
                else:
                    self.ui.external_editor(note.content, read_only=True)
            elif cmd == "e":
                # Edit within search context
                original_content = note.content  # Store original
    
                if note.is_file_note or note.created_with == "vim":
                    if note.is_file_note:
                        new_content = self.ui.external_editor(note.content, file_extension=note.file_extension)
                    else:
                        new_content = self.ui.external_editor(note.content)
                else:
                    new_content = self.ui.internal_editor(note.content)
    
                # Only save and commit if content actually changed
                if new_content is not None and new_content != original_content:
                    note.content = new_content
                    note.updated = datetime.now()
                    self.manager.save_data()

                    # 🆕 FIX: USE SMART GIT COMMIT FROM SEARCH CONTEXT
                    try:
                        root_notebook = self.manager._find_root_notebook(notebook)
                        git_manager = self.manager.get_git_manager(root_notebook.name)
                        git_manager.commit_note_edit(note.id, note.title, root_notebook.name, original_content, new_content)
                    except Exception:
                        pass
                elif new_content == original_content:
                    print("No changes made.")
                    self.ui.get_input("Press Enter to continue...")
            elif cmd == "x" and note.is_file_note:
                self.ui.export_file_note(note)
            elif cmd == "r":
                self.ui.rename_note(note)
        
        return "back"
    
    def show_search_simple(self):
        """Simple search interface - FIXED RETURN PROPAGATION"""
        self.ui.clear_screen()  # 🆕 CHANGE: Add .ui
        self.ui.print_header("Search Notes")  # 🆕 CHANGE: Add .ui

        query = self.ui.get_input("Search query: ")  # 🆕 CHANGE: Add .ui
        if not query:
            return "continue"

        # Perform search
        self.search(query)
        result = self._show_search_results_simple()
        return result if result == "exit" else "continue"
    
    def _show_search_results_simple(self):
        """Show search results with simple pagination"""
        while True:
            items_per_page = self.get_search_page_size()
            start_idx = self.current_page * items_per_page
            end_idx = start_idx + items_per_page
            total_pages = (len(self.results) + items_per_page - 1) // items_per_page
            current_page = self.current_page + 1
            paginated_results = self.results[start_idx:end_idx]

            # Display results
            self.ui.clear_screen()
            self.ui.print_header(f"Search: '{self.query}' ({len(self.results)} matches)")

            if not paginated_results:
                print("No matches found.")
            else:
                for i, result in enumerate(paginated_results, 1):
                    if result['type'] == 'current_note':
                        # EXISTING NOTE DISPLAY
                        note, notebook = self.manager.find_note_by_id(result['notebook_id'], result['note_id'])
                        if note and notebook:
                            # YOUR EXISTING PATH TRUNCATION CODE
                            notebook_path = self.manager.get_notebook_hierarchy(notebook.id)
                            if notebook_path:
                                available_width = self.ui.terminal_width - 50
                                last_two_levels = notebook_path[-2:] if len(notebook_path) >= 2 else notebook_path
                                last_two_str = "/".join([nb.name for nb in last_two_levels])
            
                                if len(last_two_str) <= available_width:
                                    if len(notebook_path) > 2:
                                        notebook_path_str = ".../" + last_two_str
                                    else:
                                        notebook_path_str = last_two_str
                                else:
                                    last_one_str = notebook_path[-1].name
                                    if len(last_one_str) <= available_width:
                                        notebook_path_str = ".../" + last_one_str
                                    else:
                                        truncated_name = last_one_str[:available_width-4] + "..."
                                        notebook_path_str = ".../" + truncated_name
                            else:
                                notebook_path_str = notebook.name

                            available_for_title = self.ui.terminal_width - len(notebook_path_str) - 30
                            display_title = note.title
                            if len(display_title) > available_for_title:
                                display_title = note.title[:available_for_title-3] + "..."

                            print(f"[{i}] {display_title} (in {notebook_path_str})")
                
                    elif result['type'] == 'current_notebook':
                        # 🆕 NEW SUBNOTEBOOK DISPLAY
                        notebook = self.manager.find_notebook_by_id(result['notebook_id'])
                        parent = self.manager.find_notebook_by_id(result['parent_id'])
                    
                        if notebook and parent:
                            note_count = notebook.get_total_note_count()
                            file_count = notebook.get_file_note_count()
                            # 🆕 ONLY SHOW COUNTS WHEN > 0
                            count_parts = []
                            if note_count > 0:
                                count_parts.append(f"{note_count} note{'s' if note_count != 1 else ''}")
                            if file_count > 0:
                                count_parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")

                            count_string = f" [{', '.join(count_parts)}]" if count_parts else ""

                            print(f"[{i}] {notebook.name} ({parent.name}){count_string}")
            
                if total_pages > 1:
                    print(f"\n--- Page {current_page}/{total_pages} ---")

            # Footer options
            footer_options = ["[B]ack", "[Q]uit"]
            if paginated_results:
                footer_options.insert(0, "[V]iew")
            if total_pages > 1:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            self.ui.print_footer("  ".join(footer_options))

            # Process input
            cmd = self.ui.get_input("> ")

            # FIXED: Smart back button - goes back through pages, then exits
            if cmd == "b":
                if self.current_page > 0:
                    # Go to previous page within search results
                    self.current_page -= 1
                else:
                    # On first page - exit search entirely
                    break
            elif cmd.startswith("v") and paginated_results:
                if cmd == "v":
                    try:
                        idx = int(self.ui.get_input("Enter result number: ")) - 1
                    except ValueError:
                        print("Invalid number")
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        print("Invalid format. Use v1, v2, etc.")
                        continue

                if 0 <= idx < len(paginated_results):
                    result = paginated_results[idx]
                
                    if result['type'] == 'current_note':
                        # EXISTING: Open note
                        note_id, notebook_id = result['note_id'], result['notebook_id']
                        self.handle_search_note_view(note_id, notebook_id, self)
                
                    elif result['type'] == 'current_notebook':
                        # 🆕 NEW: Open notebook
                        notebook_id = result['notebook_id']
                        self.show_search_notebook_view(notebook_id)
                else:
                    print("Invalid result number")
            elif cmd == "n" and current_page < total_pages:
                self.current_page += 1
            elif cmd == "p" and self.current_page > 0:
                self.current_page -= 1
            elif cmd == "q":
                confirm = self.ui.get_input("Quit Terminal Notes? [y/N]: ")
                if confirm.lower() == "y":
                    return "exit"
        
    def get_search_page_size(self):
        """Use the exact same calculation as notebook views"""
        try:
            _, terminal_height = shutil.get_terminal_size()
        
            # EXACT SAME as your working notebook view calculation
            fixed_lines = 4    # Header
            fixed_lines += 2   # Results header (equivalent to "Notes & Files") 
            fixed_lines += 2   # Page indicator (when needed)
            fixed_lines += 3   # Footer
        
            available_lines = terminal_height - fixed_lines
            items_per_page = available_lines  # NO BUFFER - fill all available lines
        
            return items_per_page
        
        except:
            return self.get_dynamic_page_size()  # Fallback to existing method
    
    def clear(self):
        self.results = []
        self.query = ""
        self.current_page = 0
    
    def search(self, query, include_historical=False):
        self.query = query
        self.results = []
        self.current_page = 0
    
        def search_recursive(notebook):
            # EXISTING: Search notes/files
            for note in notebook.notes:
                if (query.lower() in note.title.lower() or 
                    query.lower() in note.content.lower()):
                    self.results.append({
                        'type': 'current_note',
                        'note_id': note.id,
                        'notebook_id': notebook.id,
                        'item_type': 'note' if not note.is_file_note else 'file'
                    })
        
            # 🆕 NEW: Search subnotebook names
            for sub_nb in notebook.subnotebooks:
                if query.lower() in sub_nb.name.lower():
                    self.results.append({
                        'type': 'current_notebook',  # 🆕 NEW TYPE
                        'notebook_id': sub_nb.id,    # 🆕 NOTEBOOK ID
                        'parent_id': notebook.id,    # 🆕 PARENT FOR PATH
                        'item_type': 'notebook'      # 🆕 NOTEBOOK TYPE
                    })
            
                # Recursive search in subnotebook
                search_recursive(sub_nb)
    
        for notebook in self.manager.notebooks:
            search_recursive(notebook)
    
        return self.results
    
    def search_nav_push(self, screen, data=None):
        """Push to search navigation stack"""
        self.search_nav_stack.append({'screen': screen, 'data': data})

    def search_nav_pop(self):
        """Pop from search navigation stack"""
        if len(self.search_nav_stack) > 1:
            return self.search_nav_stack.pop()
        return None

    def search_nav_current(self):
        """Get current search navigation"""
        return self.search_nav_stack[-1] if self.search_nav_stack else None

    def search_nav_clear(self):
        """Clear search navigation"""
        self.search_nav_stack = []
    
    def show_search_notebook_view(self, notebook_id):
        """COMPLETELY SEPARATE notebook view for search"""
        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            return

        # 🆕 ADD PAGE TRACKING
        current_nav = self.search_nav_current()
        page = current_nav['data']['page'] if current_nav and 'page' in current_nav['data'] else 0
    
        self.search_nav_push('notebook', {'notebook_id': notebook_id, 'page': page})

        while True:
            self.ui.clear_screen()
    
            # 🆕 DYNAMIC PAGINATION (SAME AS WORKING NOTEBOOK VIEW)
            try:
                _, terminal_height = shutil.get_terminal_size()
            
                # Count ALL fixed UI elements
                fixed_lines = 4  # Header
                fixed_lines += 2  # "Notes & Files" header
                fixed_lines += 2  # Page indicator (when needed)
                fixed_lines += 3  # Footer
            
                # What's left for notes
                available_for_notes = terminal_height - fixed_lines
                items_per_page = max(1, available_for_notes - 2)  # Buffer for safety
            
            except:
                items_per_page = 8  # Fallback

            # 🆕 CALCULATE TOTAL PAGES FIRST
            total_pages = (len(notebook.notes) + items_per_page - 1) // items_per_page
        
            # 🆕 CRITICAL: VALIDATE PAGE AFTER TERMINAL RESIZE
            # If terminal was resized larger, we might be on a page that's now empty
            if page >= total_pages and total_pages > 0:
                page = total_pages - 1  # Go to last valid page
                self.search_nav_replace_page(page)
            
            # 🆕 RE-CALCULATE with corrected page
            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            paginated_notes = notebook.notes[start_idx:end_idx]

            # 🆕 SEARCH-ONLY HEADER
            notebook_path = self.manager.get_notebook_hierarchy(notebook.id)
            if notebook_path:
                path_parts = [nb.name for nb in notebook_path]
                path_str = "/".join(path_parts) + "/"
            else:
                path_str = notebook.name
    
            self.ui.print_header(f"{path_str} (search)")
    
            # 🆕 PAGINATED CONTENT DISPLAY
            if paginated_notes:
                print("Notes & Files:")
                for i, note in enumerate(paginated_notes, 1):
                    updated = note.updated.strftime("%b %d %H:%M")
                    timestamp_text = f"[Updated: {updated}]"
                    available_for_title = self.ui.terminal_width - len(timestamp_text) - len(str(i)) - 5

                    title_display = note.title
                    if len(title_display) > available_for_title:
                        title_display = title_display[:available_for_title-3] + "..."

                    padding = available_for_title - len(title_display)
                    print(f"[{i}] {title_display}{' ' * padding}{timestamp_text}")
            
                # 🆕 PAGE INDICATOR
                if total_pages > 1:
                    print(f"\n--- Page {page + 1}/{total_pages} ---")
                print()
            else:
                print("No notes or files in this notebook.")
                print()

            # 🆕 FOOTER WITH PAGINATION
            footer_options = ["[C]reate", "[B]ack to search"]
            if paginated_notes:
                footer_options.insert(1, "[V]iew")
                footer_options.append("[D]elete")
        
            # 🆕 ADD PAGINATION CONTROLS
            if total_pages > 1:
                if page > 0:
                    footer_options.insert(0, "[P]revious")
                if page < total_pages - 1:
                    footer_options.insert(0, "[N]ext")

            self.ui.print_footer("  ".join(footer_options))
        
            cmd = self.ui.get_input("> ").strip().lower()
    
            # 🆕 PAGINATION COMMANDS
            if cmd == "n" and page < total_pages - 1:
                page += 1
                self.search_nav_replace_page(page)
                continue
            elif cmd == "p" and page > 0:
                page -= 1
                self.search_nav_replace_page(page)
                continue
            elif cmd == "b":
                # 🆕 USE SEARCH NAVIGATION
                self.search_nav_pop()
                break
            elif cmd == "c":
                # 🆕 SEARCH-CONTEXT CREATE - NO SUBNOTEBOOK OPTION
                choice = self.show_search_create_choice_screen(notebook)
            
                if not choice:  # 🆕 HANDLE INVALID/CANCELLED CHOICE
                    continue
                
                if choice == "1":
                    # 🆕 STORE CURRENT STATE BEFORE CREATION
                    current_page = page
                
                    # Call create_note (it will always return to some view)
                    self.ui.create_note(notebook)
                
                    # 🆕 CHECK IF WE'RE STILL IN SEARCH NOTEBOOK VIEW
                    current_nav = self.search_nav_current()
                    if current_nav and current_nav['screen'] == 'notebook':
                        # Note was cancelled - we're still here
                        continue
                    else:
                        # Note was created - we got navigated away
                        break
                    
                elif choice == "2":
                    self.ui.create_file_note(notebook)
                    # 🆕 FILE NOTES HANDLE CANCELLATION INTERNALLY
                    self.search(self.query)
                    break

            elif cmd.startswith("v"):
                # Handle note viewing within search context
                if cmd == "v":
                    try:
                        idx = int(self.ui.get_input("Enter item number: ")) - 1
                    except ValueError:
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        continue
            
                if 0 <= idx < len(paginated_notes):
                    note = paginated_notes[idx]
                    # 🆕 PUSH NOTE VIEW TO SEARCH NAVIGATION
                    self.search_nav_push('note', {'note_id': note.id, 'notebook_id': notebook.id})
                    self.handle_search_note_view(note.id, notebook.id, self)
                    # After note view returns, we're back here
            elif cmd.startswith("d"):
                # Handle delete within search context
                if cmd == "d":
                    try:
                        idx = int(self.ui.get_input("Enter item number to delete: ")) - 1
                    except ValueError:
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        continue
            
                if 0 <= idx < len(paginated_notes):
                    note = paginated_notes[idx]
                    confirm = self.ui.get_input(f"Delete note '{note.title}'? [y/N]: ")
                    if confirm.lower() == "y":
                        notebook.notes.remove(note)
                        self.manager.save_data()
                    
                        # 🆕 CRITICAL: REFRESH SEARCH RESULTS AFTER DELETION
                        self.search(self.query)  # Re-run the same search query
                    
                        print("Note deleted. Search results updated.")
                        self.ui.get_input("Press Enter to continue...")
                        # 🆕 BREAK to reload the view with updated data
                        break
    def show_search_create_choice_screen(self, notebook):
        """Create choice screen for search context - NO SUBNOTEBOOK OPTION"""
        self.ui.clear_screen()
        self.ui.print_header(f"Create in: {notebook.name} (search)")

        print("Choose what to create:")
        print("1 - Regular Note (internal/vim editor)")
        print("2 - Specialized File (.py, .html, .sh, etc.)")
        # 🆕 NO OPTION 3 - SUBNOTEBOOK REMOVED
        print()

        choice = self.ui.get_input("Choose [1-2]: ")
        return choice if choice in ["1", "2"] else None  # 🆕 VALIDATE INPUT
    
    def search_nav_replace_page(self, page):
        """Replace current page in search navigation"""
        if self.search_nav_stack:
            self.search_nav_stack[-1]['data']['page'] = page
    