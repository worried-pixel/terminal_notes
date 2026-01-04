#!/usr/bin/env python3
import sys

sys.dont_write_bytecode = True
from datetime import datetime
import os
import shutil
import json
import re
from search_system import SimpleSearch
from git_resurrection import GitHistoryMiner
from timeline_engine import TimelineEngine

class ComprehensiveSearch:
    def __init__(self, note_manager, ui_methods):
        self.manager = note_manager
        self.ui = ui_methods
        self.simple_search = SimpleSearch(note_manager, ui_methods)
        self.history_miner = GitHistoryMiner(note_manager)
        self.timeline_engine = TimelineEngine(note_manager)  # 🆕 NEW ENGINE
        self.results = []
        self.query = ""
        self.current_page = 0
        self.search_nav_stack = []

    def search(self, query):
        self.query = query
        self.results = []
        self.current_page = 0
    
        self.history_miner.cleanup_temp_files()
    
        # ONLY CURRENT ITEMS
        current_results = self.simple_search.search(query)
    
        # ONLY LATEST DELETED ITEMS (no duplicates)
        deleted_results = self._get_unique_deleted_items(query)
    
        for result in current_results:
            enhanced = self._enhance_current_result(result)
            if enhanced:
                self.results.append(enhanced)
    
        for result in deleted_results:
            self.results.append(result)
    
        return self.results
    
    def _get_unique_deleted_items(self, query):
        """Get only TRULY deleted items (not renamed)"""
        all_deleted = self.history_miner.find_deleted_items(query)
        unique_items = {}
    
        for item in all_deleted:
            uuid_key = item.get('uuid') or item.get('item_id')
            commit_message = item.get('commit_message', '')
        
            if uuid_key and uuid_key not in unique_items:
                # Only include DELETION commits
                is_deletion_commit = 'DELETED' in commit_message.upper()
            
                if is_deletion_commit:
                    # Verify item is actually deleted from current system
                    current_note, current_notebook = self.manager.find_note_by_id(None, uuid_key)
                    is_currently_deleted = not current_note
                
                    if is_currently_deleted:
                        unique_items[uuid_key] = item
    
        return list(unique_items.values())

    def _enhance_current_result(self, result):
        if result['type'] == 'current_note':
            note, notebook = self.manager.find_note_by_id(result['notebook_id'], result['note_id'])
            if note and notebook:
                result['item_type'] = 'file' if note.is_file_note else 'note'
                result['created'] = note.created
                result['updated'] = note.updated
                result['editor'] = note.created_with
                if note.is_file_note:
                    result['file_extension'] = note.file_extension
        return result

    def show_search_simple(self):
        self.ui.clear_screen()
        self.ui.print_header("Comprehensive Search")

        query = self.ui.get_input("Search query: ")
        if not query:
            return "continue"

        self.search(query)
        result = self._show_search_results_simple()
       
        self.history_miner.cleanup_temp_files()
        
        return result if result == "exit" else "continue"

    def _show_search_results_simple(self):
        while True:
            items_per_page = self.get_search_page_size()
            start_idx = self.current_page * items_per_page
            end_idx = start_idx + items_per_page
            total_pages = (len(self.results) + items_per_page - 1) // items_per_page
            current_page = self.current_page + 1
            paginated_results = self.results[start_idx:end_idx]

            self.ui.clear_screen()
            self.ui.print_header(f"Search: '{self.query}' ({len(self.results)} matches)")

            if not paginated_results:
                print("No matches found.")
            else:
                for i, result in enumerate(paginated_results, 1):
                    display_text = self._format_result_display(result)
                    print(f"[{i}] {display_text}")

                if total_pages > 1:
                    print(f"\n--- Page {current_page}/{total_pages} ---")

            footer_options = ["[B]ack", "[Q]uit"]
            if paginated_results:
                footer_options.insert(0, "[V]iew")
            if total_pages > 1:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            self.ui.print_footer("  ".join(footer_options))

            cmd = self.ui.get_input("> ")

            if cmd == "b":
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    
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
                    navigation_result = self._handle_result_view(result)
                    
        
                    # 🆕 FIX: Break out of search loop if we navigated
                    if navigation_result == "navigate":
                       
                        break  # 🆕 Exit the while loop
                    elif navigation_result == "exit":
                        return "exit"
            elif cmd == "n" and current_page < total_pages:
                self.current_page += 1
                continue  # 🆕 ADD THIS LINE - stay in search results
            elif cmd == "p" and self.current_page > 0:
                self.current_page -= 1
                continue  # 🆕 ADD THIS LINE - stay in search results
            elif cmd == "q":
                confirm = self.ui.get_input("Quit Terminal Notes? [y/N]: ")
                if confirm.lower() == "y":
                    # 🆕 FORCE QUIT: Exit the entire app immediately
                    
                    print("Quitting Terminal Notes...")
                    self.ui.clear_screen()
                    import sys
                    sys.exit(0)
                else:
                    continue  # 🆕 Any other input cancels and stays
            # 🟢🟢🟢 PASTE THIS CHECK RIGHT HERE - AFTER PROCESSING COMMANDS
            if cmd != "" and cmd != "q":
                current_nav = self.search_nav_current()
                if current_nav and current_nav['screen'] != 'search_results':
                    screen = current_nav['screen']
                    

                if screen == 'current_note':
                    note_id = current_nav['data']['note_id']
                    page = current_nav['data']['page']
                    self._show_search_note_with_timeline(note_id, page)
                    continue

                elif screen == 'current_notebook':
                    notebook_id = current_nav['data']['notebook_id']
                    page = current_nav['data']['page']
                    resurrected_data = current_nav['data'].get('resurrected_data')                        
                        
                    if resurrected_data:
                        # 🆕 Show resurrected subnotebook
                        result = self._show_resurrected_notebook_screen(resurrected_data, page)
                    else:
                        # Regular notebook view
                        self._show_search_notebook_view(notebook_id, page)
                    continue

                elif screen == 'resurrected_note':
                    result_data = current_nav['data']['result_data']
                    self._show_resurrected_note_screen(result_data)
                    continue

                # 🆕 ADD THIS NEW CASE FOR TIMELINE VERSIONS
                elif screen == 'timeline_version':
                    timeline_data = current_nav['data']['timeline_data']
                    self._show_timeline_version_screen(timeline_data)  # 🆕 NEW METHOD
                    continue
        
        return "navigate" if self.query else "continue"
    
    def _show_resurrected_notebook_screen(self, resurrected_data, page=0):
        """Show resurrected subnotebook using its built structure"""
        # Load the notebook from temp structure
        temp_manager = self._create_temp_manager(resurrected_data['temp_dir'])
        if not temp_manager:
            print("Error: Could not load resurrected notebook")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_notebooks = temp_manager.load_all_notebooks()
        if not temp_notebooks:
            print("Error: No resurrected notebook found")
            self.ui.get_input("Press Enter to continue...")
            return

        notebook = temp_notebooks[0]
    
        # Use existing notebook view with the resurrected notebook
        self._show_resurrected_notebook_direct(notebook, page)
    
    def _show_resurrected_notebook_direct(self, notebook, page=0):
        """Show resurrected notebook directly without ID lookup - FIXED CONTENT LOADING"""        
        while True:
            self.ui.clear_screen()
    
            # 🆕 FIX: Show the ACTUAL notebook name, not the path
            header_title = f"{notebook.name}/ [RESURRECTED]"
            self.ui.print_header(header_title)
    
            # 🆕 FIX: Show BOTH notes AND subnotebooks
            if notebook.notes or notebook.subnotebooks:
                if notebook.notes:
                    print("Notes & Files:")
                    for i, note in enumerate(notebook.notes, 1):
                        # 🆕 FIX: Check if note has content before displaying
                        has_content = hasattr(note, 'content') and note.content is not None
                        content_status = " [EMPTY]" if not has_content else ""
                    
                        updated = note.updated.strftime("%b %d %H:%M") if hasattr(note, 'updated') else "Unknown"
                        timestamp_text = f"[Updated: {updated}]{content_status}"
                        available_for_title = self.ui.terminal_width - len(timestamp_text) - len(str(i)) - 5

                        title_display = note.title
                        if len(title_display) > available_for_title:
                            title_display = title_display[: available_for_title - 3] + "..."

                        padding = available_for_title - len(title_display)
                        print(f"[{i}] {title_display}{' ' * padding}{timestamp_text}")
                    print()
        
                if notebook.subnotebooks:
                    print("Sub-notebooks:")
                    next_number = len(notebook.notes) + 1
                    for i, sub_nb in enumerate(notebook.subnotebooks, next_number):
                        # 🆕 FIX: Use recursive counting for accurate numbers
                        note_count = sub_nb.get_total_note_count() if hasattr(sub_nb, 'get_total_note_count') else len(sub_nb.notes) if hasattr(sub_nb, 'notes') else 0
                        sub_count = sub_nb.get_total_subnotebook_count() if hasattr(sub_nb, 'get_total_subnotebook_count') else len(sub_nb.subnotebooks) if hasattr(sub_nb, 'subnotebooks') else 0
                
                        count_parts = []
                        if note_count > 0:
                            count_parts.append(f"{note_count} note{'s' if note_count != 1 else ''}")
                        if sub_count > 0:
                            count_parts.append(f"{sub_count} sub{'s' if sub_count != 1 else ''}")
                
                        count_string = f" ({', '.join(count_parts)})" if count_parts else ""
                        print(f"[{i}] {sub_nb.name}{count_string}")
                    print()
            else:
                print("This notebook is empty.")
                print("It was deleted before any content was added.")
                print()

            # Footer
            footer_options = ["[B]ack"]
            if notebook.notes or notebook.subnotebooks:
                footer_options.insert(0, "[V]iew")

            self.ui.print_footer("  ".join(footer_options))

            cmd = self.ui.get_input("> ").strip().lower()

            if cmd == "b":
                break
            elif cmd.startswith("v") and (notebook.notes or notebook.subnotebooks):
                # Handle both notes and subnotebook viewing
                total_items = len(notebook.notes) + len(notebook.subnotebooks)
                if cmd == "v":
                    try:
                        idx = int(self.ui.get_input(f"Enter item number [1-{total_items}]: ")) - 1
                    except ValueError:
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        continue

                if 0 <= idx < total_items:
                    if idx < len(notebook.notes):
                        # It's a note - view it directly
                        note = notebook.notes[idx]
                        self._show_resurrected_note_from_subnotebook(note, notebook)
                    else:
                        # It's a subnotebook
                        sub_idx = idx - len(notebook.notes)
                        sub_nb = notebook.subnotebooks[sub_idx]
                        self._show_resurrected_notebook_direct(sub_nb, 0)
                        
    def _show_resurrected_note_from_subnotebook(self, note, parent_notebook):
        """Show a resurrected note that's inside a resurrected subnotebook"""
        result_data = {
            'type': 'resurrected_note',
            'title': note.title,
            'content': getattr(note, 'content', ''),
            'file_extension': getattr(note, 'file_extension', None),
            'uuid': note.id,
            'is_file_note': hasattr(note, 'file_extension') and note.file_extension is not None,
            'is_subnotebook': False,
            'is_nested_note': True,
            'parent_notebook': parent_notebook
        }
    
        # 🆕 PUSH TO NAVIGATION STACK FOR PROPER PAGE MANAGEMENT
        self.search_nav_push('nested_resurrected_note', {
            'result_data': result_data,
            'page': 0  # Start at page 0
        })
    
        self._show_nested_resurrected_note(result_data)
    
    def _show_nested_resurrected_note(self, result_data):
        """Show a resurrected note that's nested inside a subnotebook - PERFECT PAGINATION"""
        note_content = result_data.get('content', '')
        note_title = result_data.get('title', 'Unknown')
        is_file_note = result_data.get('is_file_note', False)
        file_extension = result_data.get('file_extension')
    
        current_nav = self.search_nav_current()
        page = current_nav['data']['page'] if current_nav and 'page' in current_nav['data'] else 0

        while True:
            # 🆕 USE EXACT SAME APPROACH AS REGULAR NOTES
            terminal_width, terminal_height = shutil.get_terminal_size()
            self.ui.clear_screen()

            # 🆕 IDENTICAL HEADER TO NORMAL NOTES
            separator = "=" * terminal_width
            print(separator)
        
            header_title = f"{note_title} [NESTED IN RESURRECTED SUBNOTEBOOK]"
            print(f"{header_title:^{terminal_width}}")
            print(separator)

            # 🆕 IDENTICAL NOTE INFO TO NORMAL NOTES
            if is_file_note:
                ext_display = f".{file_extension} file" if file_extension else "file"
                print(f"File Name: {note_title} [{ext_display}]")
            else:
                print(f"Note Title: {note_title}")

            print(f"Status: Resurrected from Git history")

            # 🆕 IDENTICAL SEPARATOR
            print("-" * terminal_width)

            # 🆕 USE UI'S EXACT PAGINATION CALCULATION
            pagination_info = self.ui.calculate_note_pagination(note_content, terminal_height)
            wrapped_lines = pagination_info['wrapped_lines']
            available_content_lines = pagination_info['available_content_lines']
            needs_pagination = pagination_info['needs_pagination']
            total_pages = pagination_info['total_pages']

            max_content_lines = int(available_content_lines * 0.9)
            max_content_lines = max(1, max_content_lines)

            if needs_pagination:
                if page >= total_pages:
                    page = total_pages - 1
                    if current_nav:
                        current_nav['data']['page'] = page
        
                start_idx = page * max_content_lines
                end_idx = start_idx + max_content_lines
                paginated_lines = wrapped_lines[start_idx:end_idx]
                current_page = page + 1
            else:
                if page > 0:
                    page = 0
                    if current_nav:
                        current_nav['data']['page'] = page
                paginated_lines = wrapped_lines
                current_page = 1
                total_pages = 1

            # 🆕 IDENTICAL CONTENT DISPLAY TO NORMAL NOTES
            for line in paginated_lines:
                print(line)

            # 🆕 IDENTICAL PAGE INDICATOR TO NORMAL NOTES
            if needs_pagination:
                print(f"--- Page {current_page} of {total_pages} ---")
                print()

            # 🆕 OPTIMIZED FOOTER
            print("-" * terminal_width)

            footer_options = ["[V]iew", "[B]ack"]
        
            if is_file_note:
                footer_options.insert(1, "[X]port")

            if needs_pagination:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            print("  ".join(footer_options))
            print()

            cmd = self.ui.get_input("> ").strip().lower()

            # 🆕 IDENTICAL COMMAND PROCESSING TO NORMAL NOTES
            if cmd == "b":
                break
            elif cmd == "p" and page > 0:
                page -= 1
                if current_nav:
                    current_nav['data']['page'] = page
            elif cmd == "n" and current_page < total_pages:
                page += 1
                if current_nav:
                    current_nav['data']['page'] = page
            elif cmd == "v":
                try:
                    if is_file_note:
                        self.ui.external_editor(
                            note_content, 
                            read_only=True, 
                            file_extension=file_extension
                        )
                    else:
                        self.ui.external_editor(note_content, read_only=True)
                except Exception as e:
                    print(f"Error opening editor: {str(e)}")
                    self.ui.get_input("Press Enter to continue...")
            elif cmd == "x" and is_file_note:
                self._export_nested_file_note(note_title, note_content, file_extension)
                
    def _export_nested_file_note(self, filename, content, file_extension=None):
        """Export a nested file note"""
        self.ui.clear_screen()
        self.ui.print_header(f"Export File: {filename}")

        print("Enter export directory:")
        print("Examples: /tmp/ ~/Downloads/ ./")
        print()
    
        export_dir = self.ui.get_input("Export directory: ")
        if not export_dir:
            return
    
        export_dir = os.path.expanduser(export_dir)
        export_path = os.path.join(export_dir, filename)

        try:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"File exported successfully to: {export_path}")
        except Exception as e:
            print(f"Export failed: {e}")
    
        self.ui.get_input("Press Enter to continue...")
    
    def _show_resurrected_note_direct(self, note, notebook):
        """Show a resurrected note directly"""
        # Create a result_data structure similar to what _handle_resurrected_view expects
        result_data = {
            'type': 'resurrected_note',
            'title': note.title,
            'content': note.content if hasattr(note, 'content') else "",
            'file_extension': getattr(note, 'file_extension', None),
            'uuid': note.id,
            'notebook_path': "",  # Not available in direct call
            'temp_dir': "",  # Not available in direct call
            'is_file_note': hasattr(note, 'file_extension') and note.file_extension is not None
        }
    
        self._show_resurrected_note_screen(result_data)
    
    def _show_search_notebook_view(self, notebook_id, page=0):
        """Show notebook view within comprehensive search context"""
        notebook = self.manager.find_notebook_by_id(notebook_id)
        if not notebook:
            return "back"

        while True:
            # Use the same UI method as regular notebook view but in search context
            self.ui.clear_screen()
        
            # Build header with search context
            notebook_path = self.manager.get_notebook_hierarchy(notebook.id)
            if notebook_path:
                path_parts = [nb.name for nb in notebook_path]
                path_str = "/".join(path_parts) + "/"
            else:
                path_str = notebook.name
            
            self.ui.print_header(f"{path_str} (search)")
        
            # Show immediate content only (no deeper subnotebooks)
            if notebook.notes:
                print("Notes & Files:")
                for i, note in enumerate(notebook.notes, 1):
                    updated = note.updated.strftime("%b %d %H:%M")
                    timestamp_text = f"[Updated: {updated}]"
                    available_for_title = self.ui.terminal_width - len(timestamp_text) - len(str(i)) - 5

                    title_display = note.title
                    if len(title_display) > available_for_title:
                        title_display = title_display[:available_for_title-3] + "..."

                    padding = available_for_title - len(title_display)
                    print(f"[{i}] {title_display}{' ' * padding}{timestamp_text}")
                print()
            else:
                print("No notes or files in this notebook.")
                print()

            # Search-specific footer (no create subnotebook option)
            footer_options = ["[B]ack to search"]
            if notebook.notes:
                footer_options.insert(0, "[V]iew")
                footer_options.insert(-1, "[D]elete")

            self.ui.print_footer("  ".join(footer_options))

            cmd = self.ui.get_input("> ").strip().lower()

            if cmd == "b":
                self.search_nav_pop()
                break
            elif cmd.startswith("v"):
                # Handle note viewing
                if cmd == "v":
                    try:
                        idx = int(self.ui.get_input("Enter note number: ")) - 1
                    except ValueError:
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        continue
        
                if 0 <= idx < len(notebook.notes):
                    note = notebook.notes[idx]
                    # 🆕 DIRECT CALL to note view (simpler approach)
                    self._show_search_note_with_timeline(note.id, notebook.id)
                    # After note view returns, we stay in notebook view
            elif cmd.startswith("d"):
                # Handle delete
                if cmd == "d":
                    try:
                        idx = int(self.ui.get_input("Enter note number to delete: ")) - 1
                    except ValueError:
                        continue
                else:
                    try:
                        idx = int(cmd[1:]) - 1
                    except ValueError:
                        continue
        
                if 0 <= idx < len(notebook.notes):
                    note = notebook.notes[idx]
                    confirm = self.ui.get_input(f"Delete note '{note.title}'? [y/N]: ")
                    if confirm.lower() == "y":
                        notebook.notes.remove(note)
                        self.manager.save_data()
                    
                        # Git commit for deletion
                        try:
                            root_notebook = self.manager._find_root_notebook(notebook)
                            git_manager = self.manager.get_git_manager(root_notebook.name)
                            git_manager.commit_note_deletion(note.id, note.title, root_notebook.name, note.is_file_note)
                        except Exception:
                            pass
                    
                        print("Note deleted.")
                        self.ui.get_input("Press Enter to continue...")
                        # Stay in the notebook view with updated content

        return "continue"
    
    def _show_search_note_with_timeline(self, note_id, page=0):
        """Show current note with identical layout to normal notes + timeline"""
        # 🆕 FIX: Ensure page is integer
        if isinstance(page, str):
            try:
                page = int(page)
            except ValueError:
                page = 0
        elif page is None:
            page = 0
        note, notebook = self.manager.find_note_by_id(None, note_id)
        if not note or not notebook:
            return "continue"

        while True:
            # 🆕 USE EXACT SAME PAGINATION AS NORMAL NOTES
            terminal_width, terminal_height = shutil.get_terminal_size()
            self.ui.clear_screen()

            # 🆕 IDENTICAL HEADER
            separator = "=" * terminal_width
            print(separator)
        
            smart_path = self.ui.get_smart_header_path(notebook.id)
            print(f"{smart_path:^{terminal_width}}")
            print(separator)

            # 🆕 IDENTICAL NOTE INFO
            if note.is_file_note:
                print(f"File Name: {note.title} [.{note.file_extension} file]")
            else:
                print(f"Note Title: {note.title}")

            timestamp = note.updated.strftime("%b %d %H:%M")
            created = note.created.strftime("%b %d")
            print(f"Created: {created}  Updated: {timestamp}")

            # 🆕 IDENTICAL SEPARATOR
            print("-" * terminal_width)

            # 🆕 IDENTICAL CONTENT PAGINATION (from normal note view)
            pagination_info = self.ui.calculate_note_pagination(note.content, terminal_height)
            wrapped_lines = pagination_info['wrapped_lines']
            available_content_lines = pagination_info['available_content_lines']
            needs_pagination = pagination_info['needs_pagination']
            total_pages = pagination_info['total_pages']

            max_content_lines = int(available_content_lines * 0.9)
            max_content_lines = max(1, max_content_lines)

            if needs_pagination:
                if page >= total_pages:
                    page = total_pages - 1
            
                start_idx = page * max_content_lines
                end_idx = start_idx + max_content_lines
                paginated_lines = wrapped_lines[start_idx:end_idx]
                current_page = page + 1
            else:
                if page > 0:
                    page = 0
                paginated_lines = wrapped_lines
                current_page = 1
                total_pages = 1

            # 🆕 IDENTICAL CONTENT DISPLAY
            for line in paginated_lines:
                print(line)

            # 🆕 IDENTICAL PAGE INDICATOR
            if needs_pagination:
                print(f"--- Page {current_page} of {total_pages} ---")
                print()

            # 🆕 OPTIMIZED FOOTER FOR SEARCH CONTEXT
            print("-" * terminal_width)

            footer_options = ["[E]dit", "[V]iew", "[T]imeline", "[B]ack"]
            if note.is_file_note:
                footer_options.insert(3, "[X]port")  # Add export before back
            footer_options.insert(-1, "[R]ename")  # Add rename before back

            if needs_pagination:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            print("  ".join(footer_options))
            print()

            cmd = self.ui.get_input("> ").strip().lower()

            # 🆕 IDENTICAL COMMAND PROCESSING + TIMELINE
            if cmd == "b":
                break
            elif cmd == "p" and page > 0:
                page -= 1
            elif cmd == "n" and current_page < total_pages:
                page += 1
            elif cmd == "e":
                # 🆕 ACTUAL EDIT LOGIC
                original_content = note.content
                if note.is_file_note:
                    new_content = self.ui.external_editor(note.content, file_extension=note.file_extension)
                else:
                    new_content = self.ui.external_editor(note.content)
                
                if new_content is not None and new_content != original_content:
                    note.content = new_content
                    note.updated = datetime.now()
                    self.manager.save_data()
                    
                    # Git commit for edit
                    try:
                        root_notebook = self.manager._find_root_notebook(notebook)
                        git_manager = self.manager.get_git_manager(root_notebook.name)
                        git_manager.commit_note_edit(note.id, note.title, root_notebook.name, original_content, new_content)
                    except Exception:
                        pass
                    # 🆕 REFRESH SEARCH RESULTS
                    break
            
            elif cmd == "v":
                # 🆕 ACTUAL VIEW LOGIC
                if note.is_file_note:
                    self.ui.external_editor(note.content, read_only=True, file_extension=note.file_extension)
                else:
                    self.ui.external_editor(note.content, read_only=True)
            
            elif cmd == "r":
                # 🆕 USE EXISTING RENAME FUNCTIONALITY  
                self.ui.rename_note(note)
                # 🆕 REFRESH SEARCH RESULTS
                break
            
            elif cmd == "x" and note.is_file_note:
                # 🆕 USE EXISTING EXPORT FUNCTIONALITY
                self.ui.export_file_note(note)
            elif cmd == "t":
                # 🆕 FIX: Use timeline engine directly with proper parameters
                self.show_note_timeline(note.id, notebook.id)

        return "continue"

    def _handle_result_view(self, result):
        """Handle viewing any type of result - NUCLEAR FIX"""
    

        if result['type'] == 'resurrected_note':
            if result.get('is_subnotebook') is True:
                
                # 🚀 NUCLEAR: Call the viewer directly, no navigation stack
                self._show_resurrected_notebook_screen(result, 0)
                return "navigate"
            else:
                
                # 🚀 NUCLEAR: Call the viewer directly
                self._show_resurrected_note_screen(result)
                return "navigate"
                
        elif result['type'] == 'timeline_version':
            
            self._show_timeline_version_screen(result['timeline_data'])
            return "navigate"
            
        elif result['type'] == 'current_note':
           
            self._show_search_note_with_timeline(result['note_id'], 0)
            return "navigate"
            
        elif result['type'] == 'current_notebook':
            
            self._show_search_notebook_view(result['notebook_id'], 0)
            return "navigate"
        
        return "continue"

    # 🆕 ADD THIS NEW METHOD RIGHT AFTER _handle_result_view
    def _create_timeline_version(self, result):
        """Create temporary data for timeline version using existing resurrection"""
        return self.history_miner._create_temp_json_for_item(
            result['notebook_path'],
            result['note_id'], 
            result['commit_hash'],
            result['message']
        )

    def _handle_resurrected_view(self, result):
        """View a resurrected item with proper error handling"""
        
        try:
            temp_dir = result.get('temp_dir')
            if not temp_dir or not os.path.exists(temp_dir):
                print("Error: Resurrected item data not available")
                self.ui.get_input("Press Enter to continue...")
                return

            temp_manager = self._create_temp_manager(temp_dir)
            if not temp_manager:
                print("Error: Could not load resurrected item")
                self.ui.get_input("Press Enter to continue...")
                return

            # Load the resurrected notebook
            temp_notebooks = temp_manager.load_all_notebooks()
            if not temp_notebooks:
                print("Error: No resurrected data found")
                self.ui.get_input("Press Enter to continue...")
                return

            temp_notebook = temp_notebooks[0]
            if not temp_notebook.notes:
                print("Error: No resurrected notes found")
                self.ui.get_input("Press Enter to continue...")
                return

            resurrected_note = temp_notebook.notes[0]
        
            # 🆕 CRITICAL: Verify note has content before displaying
            if not hasattr(resurrected_note, 'content'):
                print("Error: Resurrected note has no content attribute")
                self.ui.get_input("Press Enter to continue...")
                return
            
            self._show_resurrected_note_screen(resurrected_note, temp_notebook, result)
        
        except Exception as e:
            # 🆕 CRITICAL: Show the error instead of hiding it
            print(f"Error viewing resurrected item: {str(e)}")
            import traceback
            traceback.print_exc()  # 🆕 This will show the full error stack
            self.ui.get_input("Press Enter to continue...")

    def _create_temp_manager(self, temp_dir):
        """Simplified temporary manager - without setting read-only properties"""
        class TempNoteManager:
            def __init__(self, temp_dir):
                self.notebooks_root = temp_dir
                self.notebooks = []
                self._load_simple_notebooks()
        
            def _load_simple_notebooks(self):
                from terminal_notes_core import Notebook
                import json
                import os
            
                structure_file = os.path.join(self.notebooks_root, "structure.json")
                notes_file = os.path.join(self.notebooks_root, "notes.json")
                files_file = os.path.join(self.notebooks_root, "files.json")
            
                if not os.path.exists(structure_file):
                    return
                
                # Load structure
                with open(structure_file, "r") as f:
                    structure_data = json.load(f)
            
                # Load content maps
                notes_map = {}
                files_map = {}
            
                if os.path.exists(notes_file):
                    with open(notes_file, "r") as f:
                        notes_map = json.load(f)
            
                if os.path.exists(files_file):
                    with open(files_file, "r") as f:
                        files_map = json.load(f)
            
                # Create notebooks and apply content
                for nb_data in structure_data.get('notebooks', []):
                    # 🆕 FIX: Check if this is a notebook or note
                    if 'name' in nb_data and ('subnotebooks' in nb_data or 'notes' in nb_data):
                        # This is a notebook/subnotebook
                        notebook = Notebook.from_dict(nb_data)
                    elif 'title' in nb_data:
                        # This is a note - should not happen in notebooks list, but handle gracefully
                        continue
                    else:
                        # Unknown type - skip
                        continue
                
                    # Apply content to all notes in this notebook
                    for note in notebook.notes:
                        note_id = note.id
                    
                        # 🆕 FIX: Use hasattr to check for file_extension instead of setting is_file_note
                        is_file_note = hasattr(note, 'file_extension') and note.file_extension is not None
                    
                        if is_file_note:
                            # File note - get from files.json
                            if note_id in files_map:
                                note.content = files_map[note_id]
                        else:
                            # Regular note - get from notes.json
                            if note_id in notes_map:
                                note.content = notes_map[note_id]
                        # 🆕 REMOVED: Don't try to set is_file_note - it's a read-only property
                
                    self.notebooks.append(notebook)
            
                return self.notebooks
        
            def load_all_notebooks(self):
                return self.notebooks
        
            def get_notebook_folder_path(self, notebook_name):
                return self.notebooks_root
    
        return TempNoteManager(temp_dir)

    def _show_resurrected_note_screen(self, result_data):
        """Show resurrected note with READ-ONLY layout identical to regular notes"""
        # Extract note and notebook from result_data
        temp_dir = result_data.get('temp_dir')
        if not temp_dir or not os.path.exists(temp_dir):
            print("Error: Resurrected item data not available")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_manager = self._create_temp_manager(temp_dir)
        if not temp_manager:
            print("Error: Could not load resurrected item")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_notebooks = temp_manager.load_all_notebooks()
        if not temp_notebooks:
            print("Error: No resurrected data found")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_notebook = temp_notebooks[0]
        if not temp_notebook.notes:
            print("Error: No resurrected notes found")
            self.ui.get_input("Press Enter to continue...")
            return

        note = temp_notebook.notes[0]
        notebook = temp_notebook

        current_nav = self.search_nav_current()
        page = current_nav['data']['page'] if current_nav and 'page' in current_nav['data'] else 0

        while True:
            # Get terminal size
            terminal_width, terminal_height = shutil.get_terminal_size()
            self.ui.clear_screen()

            # 🆕 USE UI'S CALCULATE_NOTE_PAGINATION FOR CONSISTENCY
            content = note.content if hasattr(note, 'content') and note.content else ""
            pagination_info = self.ui.calculate_note_pagination(content, terminal_height)
            wrapped_lines = pagination_info['wrapped_lines']
            available_content_lines = pagination_info['available_content_lines']
            needs_pagination = pagination_info['needs_pagination']
            total_pages = pagination_info['total_pages']

            max_content_lines = int(available_content_lines * 0.9)
            max_content_lines = max(1, max_content_lines)

            if needs_pagination:
                if page >= total_pages:
                    page = total_pages - 1
                    current_nav['data']['page'] = page
        
                start_idx = page * max_content_lines
                end_idx = start_idx + max_content_lines
                paginated_lines = wrapped_lines[start_idx:end_idx]
                current_page = page + 1
            else:
                if page > 0:
                    page = 0
                    current_nav['data']['page'] = page
                paginated_lines = wrapped_lines
                current_page = 1
                total_pages = 1

            # 🆕 IDENTICAL HEADER TO NORMAL NOTES
            separator = "=" * terminal_width
            print(separator)
    
            # Build path like regular notes but mark as resurrected
            notebook_path = self.manager.get_notebook_hierarchy(notebook.id) if hasattr(notebook, 'id') else []
            if notebook_path:
                path_parts = [nb.name for nb in notebook_path]
                path_str = "/".join(path_parts) + "/"
            else:
                path_str = "Resurrected/"

            header_title = f"{path_str} [RESURRECTED]"
            print(f"{header_title:^{terminal_width}}")
            print(separator)

            # 🆕 IDENTICAL NOTE INFO TO NORMAL NOTES
            is_file_note = hasattr(note, 'file_extension') and note.file_extension is not None

            if is_file_note:
                print(f"File Name: {note.title} [.{note.file_extension} file]")
            else:
                print(f"Note Title: {note.title}")

            # Show timestamps like regular notes
            if hasattr(note, 'updated'):
                timestamp = note.updated.strftime("%b %d %H:%M")
                created = note.created.strftime("%b %d")
                print(f"Created: {created}  Updated: {timestamp}")
            else:
                print(f"Status: Resurrected from Git history")

            # 🆕 IDENTICAL SEPARATOR
            print("-" * terminal_width)

            # 🆕 IDENTICAL CONTENT DISPLAY TO NORMAL NOTES
            for line in paginated_lines:
                print(line)

            # 🆕 IDENTICAL PAGE INDICATOR TO NORMAL NOTES
            if needs_pagination:
                print(f"--- Page {current_page} of {total_pages} ---")
                print()

            # 🆕 MODIFIED FOOTER: READ-ONLY ONLY
            print("-" * terminal_width)

            footer_options = ["[V]iew", "[T]imeline", "[B]ack to search"]
    
            # 🆕 ONLY SHOW EXPORT FOR FILE NOTES (no edit/rename)
            if is_file_note:
                footer_options.insert(1, "[X]port")
    
            # 🆕 NO [E]dit, NO [R]ename buttons
    
            if needs_pagination:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            print("  ".join(footer_options))
            print()

            cmd = self.ui.get_input("> ").strip().lower()

            if cmd == "b":
                self.search_nav_pop()
                break
            elif cmd == "p" and page > 0:
                page -= 1
                self.search_nav_current()['data']['page'] = page
            elif cmd == "n" and current_page < total_pages:
                page += 1
                self.search_nav_current()['data']['page'] = page
            elif cmd == "v":
                try:
                    # 🆕 IDENTICAL VIEW LOGIC TO NORMAL NOTES
                    if is_file_note:
                        self.ui.external_editor(
                            note.content if hasattr(note, 'content') else "", 
                            read_only=True, 
                            file_extension=note.file_extension
                        )
                    else:
                        self.ui.external_editor(
                            note.content if hasattr(note, 'content') else "", 
                            read_only=True
                        )
                except Exception as e:
                    print(f"Error opening editor: {str(e)}")
                    self.ui.get_input("Press Enter to continue...")
            elif cmd == "x" and is_file_note:
                self._export_resurrected_file(note, result_data)
            elif cmd == "t":
                # 🆕 FIX: Get proper notebook context for timeline
                original_uuid = result_data.get('uuid')
                notebook_path = result_data.get('notebook_path')
    
                if original_uuid and notebook_path:
                    # Find the notebook by path/name
                    notebook_name = os.path.basename(notebook_path)
                    notebook = None
        
                    # Search for the notebook in manager
                    for nb in self.manager.notebooks:
                        nb_path = self.manager.get_notebook_folder_path(nb.name)
                        if nb_path == notebook_path or nb.name == notebook_name:
                            notebook = nb
                            break
        
                    if notebook:
                        self.show_note_timeline(original_uuid, notebook.id)
                    else:
                        print("Cannot find original notebook for timeline")
                        self.ui.get_input("Press Enter to continue...")
                else:
                    print("Cannot show timeline for this item")
                    self.ui.get_input("Press Enter to continue...")

    def _export_resurrected_file(self, note, result_data):
        self.ui.clear_screen()
        self.ui.print_header(f"Export Resurrected File: {note.title}")
        
        print("Enter export directory:")
        print("Examples: /tmp/ ~/Downloads/ ./")
        print()
        
        export_dir = self.ui.get_input("Export directory: ")
        if not export_dir:
            return
        
        export_dir = os.path.expanduser(export_dir)
        export_path = os.path.join(export_dir, note.title)
        
        try:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(note.content)
            print(f"File exported successfully to: {export_path}")
        except Exception as e:
            print(f"Export failed: {e}")
        
        self.ui.get_input("Press Enter to continue...")

    def _format_result_display(self, result):
        if result['type'] == 'resurrected_note':
            return self._format_resurrected_result(result)
        else:
            return self._format_current_result(result)

    def _format_resurrected_result(self, result):
        title = result['title']
        notebook_name = os.path.basename(result['notebook_path'])
    
        # 🆕 CLEANEST FORMAT - just show it's deleted
        available_for_title = self.ui.terminal_width - len(notebook_name) - 25  # " (deleted from )"
        if len(title) > available_for_title:
            title = title[:available_for_title-3] + "..."
    
        # 🆕 SIMPLE: Just show it's deleted, no extra tags
        return f"{title} (deleted from {notebook_name})"

    def _format_current_result(self, result):
        if result['type'] == 'current_note':
            note, notebook = self.manager.find_note_by_id(result['notebook_id'], result['note_id'])
            if note and notebook:
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

                # 🆕 REMOVE enhanced info from search results
                return f"{display_title} (in {notebook_path_str})"
                
        elif result['type'] == 'current_notebook':
            notebook = self.manager.find_notebook_by_id(result['notebook_id'])
            parent = self.manager.find_notebook_by_id(result['parent_id'])
        
            if notebook and parent:
                # 🆕 SHOW IMMEDIATE CONTENT ONLY (like quick search)
                immediate_notes = notebook.notes
                immediate_note_count = len(immediate_notes)
                immediate_file_count = sum(1 for note in immediate_notes if note.is_file_note)
                immediate_regular_count = immediate_note_count - immediate_file_count
                
                content_parts = []
                if immediate_regular_count > 0:
                    content_parts.append(f"{immediate_regular_count} note{'s' if immediate_regular_count != 1 else ''}")
                if immediate_file_count > 0:
                    content_parts.append(f"{immediate_file_count} file{'s' if immediate_file_count != 1 else ''}")
                
                content_string = f" ({', '.join(content_parts)})" if content_parts else ""
                
                return f"{notebook.name} ({parent.name}){content_string}"
        
        return "Unknown result type"

    def _get_enhanced_info(self, result):
        info_parts = []
        
        if result.get('file_extension'):
            info_parts.append(result['file_extension'].upper())
            
        if result.get('editor') == 'vim':
            info_parts.append('vim')
            
        if result.get('created'):
            days_ago = (datetime.now() - result['created']).days
            if days_ago == 0:
                info_parts.append('today')
            elif days_ago == 1:
                info_parts.append('yesterday')
            elif days_ago < 7:
                info_parts.append(f'{days_ago}d')
                
        return f"[{', '.join(info_parts)}]" if info_parts else ""

    def get_search_page_size(self):
        try:
            _, terminal_height = shutil.get_terminal_size()
            fixed_lines = 4 + 2 + 2 + 3
            available_lines = terminal_height - fixed_lines
            return max(1, available_lines)
        except:
            return 20

    def search_nav_push(self, screen, data=None):
        if not hasattr(self, 'search_nav_stack'):
            self.search_nav_stack = []
        self.search_nav_stack.append({'screen': screen, 'data': data})

    def search_nav_pop(self):
        if hasattr(self, 'search_nav_stack') and self.search_nav_stack:
            return self.search_nav_stack.pop()
        return None

    def search_nav_current(self):
        if hasattr(self, 'search_nav_stack') and self.search_nav_stack:
            return self.search_nav_stack[-1]
        return None

    def clear(self):
        self.results = []
        self.query = ""
        self.current_page = 0
        
    def show_note_timeline(self, note_id, notebook_id):
        """Show timeline for a specific note - ISOLATED VERSION"""
        
        # 🆕 FIX: Save current search state
        original_results = self.results.copy()
        original_query = self.query
        original_page = self.current_page
    
        try:
            # Get timeline using the engine
            timeline_versions = self.timeline_engine.get_item_timeline(note_id, notebook_id)
    
            if not timeline_versions:
                print("No history found for this note")
                self.ui.get_input("Press Enter to continue...")
                return "continue"
    
            # 🆕 FIX: Use temporary variables, don't modify main search state
            timeline_results = []
            for version in timeline_versions:
                timeline_results.append({
                    'type': 'timeline_version',
                    'timeline_data': version,
                    'commit_hash': version['commit_hash'],
                    'date': version['date'], 
                    'message': version['commit_message'],
                    'note_id': note_id,
                    'notebook_path': version['notebook_path'],
                    'timeline_index': len(timeline_results) + 1
                })
    
            # 🆕 FIX: Temporarily set state for timeline display only
            self.results = timeline_results
            # 🆕 FIX: Show actual note/file name in timeline header
            note, notebook = self.manager.find_note_by_id(None, note_id)
            if note:
                item_name = note.title
                if note.is_file_note:
                    item_type = "file"
                else:
                    item_type = "note"
                self.query = f"Timeline for {item_type}: {item_name}"
            else:
                self.query = f"Timeline for item"
            self.current_page = 0
    
            # Show timeline results
            return self._show_timeline_results()
    
        finally:
            # 🆕 CRITICAL: Always restore original search state
            self.results = original_results
            self.query = original_query
            self.current_page = original_page
    
    def _handle_timeline_version_view(self, timeline_data):
        """Handle viewing any timeline version using the engine data"""
        # 🆕 USE THE PRE-BUILT TIMELINE DATA
        if timeline_data['item_type'] in ['note', 'file']:
            self._show_timeline_note_screen(timeline_data)
        elif timeline_data['item_type'] in ['notebook', 'subnotebook']:
            self._show_timeline_notebook_screen(timeline_data)

    def _show_timeline_results(self):
        """Show timeline results - FIXED VERSION"""
        
        # Temporarily override formatting for timeline
        original_format_method = self._format_result_display

        def timeline_formatter(result):
            if result['type'] == 'timeline_version':
                date_str = result.get('date', datetime.now()).strftime("%Y-%m-%d %H:%M")
                message = result.get('message', '') or result.get('commit_message', '')
            
                if 'CREATED' in message:
                    action = 'CREATED'
                    # Extract creation details
                    if 'Editor:' in message:
                        editor_match = re.search(r'Editor:\s*([^\n,]+)', message)
                        editor = editor_match.group(1) if editor_match else 'unknown'
                    
                        lines_match = re.search(r'Lines:\s*(\d+)', message)
                        lines = lines_match.group(1) if lines_match else '?'
                    
                        details = f"({editor}, {lines} lines)"
                    else:
                        details = '(created)'
                    
                elif 'UPDATED' in message:
                    action = 'EDITED'
                    # Extract changes
                    lines_match = re.search(r'Lines:\s*(\d+)\s*→\s*(\d+)\s*\(([+-]\d+)\)', message)
                    words_match = re.search(r'Words:\s*(\d+)\s*→\s*(\d+)\s*\(([+-]\d+)\)', message)
                
                    changes = []
                    if lines_match and lines_match.group(3) != '+0':
                        changes.append(f"{lines_match.group(3)} lines")
                    if words_match and words_match.group(3) != '+0':
                        changes.append(f"{words_match.group(3)} words")
                    
                    details = f"({', '.join(changes)})" if changes else '(no changes)'
                
                elif 'RENAMED' in message:
                    action = 'RENAMED'
                    rename_match = re.search(r'RENAMED\s+\w+:\s*([^→]+)→\s*([^|]+)', message)
                    if rename_match:
                        old_name = rename_match.group(1).strip()
                        new_name = rename_match.group(2).strip()
                    
                        max_name_len = 12
                        if len(old_name) > max_name_len:
                            old_name = old_name[:max_name_len-3] + '...'
                        if len(new_name) > max_name_len:
                            new_name = new_name[:max_name_len-3] + '...'
                        
                        details = f"({old_name} → {new_name})"
                    else:
                        details = '(renamed)'
                    
                elif 'DELETED' in message:
                    action = 'DELETED'
                    details = '(deleted)'
                
                else:
                    action = 'MODIFIED'
                    details = '(modified)'
                
                # Format display
                max_details_width = 35
                if len(details) > max_details_width:
                    details = details[:max_details_width-3] + '...'
                
                action_padding = 12 - len(action)
                display_text = f"{date_str} {action}{' ' * action_padding}{details}"
            
                return display_text
            return original_format_method(result)

        self._format_result_display = timeline_formatter
    
        # 🆕 CRITICAL: USE THE SAME SEARCH RESULTS BUT WITH PROPER VIEW HANDLING
        result = self._show_search_results_simple()
    
        # Restore original formatter
        self._format_result_display = original_format_method
    
        return result
    
    def _show_timeline_version_screen(self, timeline_data):
        """Show a specific timeline version - ACTUAL COMMIT CONTENT"""
        if not timeline_data or 'temp_dir' not in timeline_data:
            print("Error: Timeline version data not available")
            self.ui.get_input("Press Enter to continue...")
            return

        # 🆕 USE THE SAME METHOD AS RESURRECTED NOTES BUT WITH TIMELINE DATA
        temp_dir = timeline_data['temp_dir']
        if not temp_dir or not os.path.exists(temp_dir):
            print("Error: Historical version data not available")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_manager = self._create_temp_manager(temp_dir)
        if not temp_manager:
            print("Error: Could not load historical version")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_notebooks = temp_manager.load_all_notebooks()
        if not temp_notebooks:
            print("Error: No historical data found")
            self.ui.get_input("Press Enter to continue...")
            return

        temp_notebook = temp_notebooks[0]
        if not temp_notebook.notes:
            print("Error: No historical notes found")
            self.ui.get_input("Press Enter to continue...")
            return

        note = temp_notebook.notes[0]
        notebook = temp_notebook

        current_nav = self.search_nav_current()
        page = current_nav['data']['page'] if current_nav and 'page' in current_nav['data'] else 0

        while True:
            terminal_width, terminal_height = shutil.get_terminal_size()
            self.ui.clear_screen()

            # 🆕 USE THE RESURRECTED CONTENT, NOT CURRENT CONTENT
            content = note.content if hasattr(note, 'content') and note.content else ""
            pagination_info = self.ui.calculate_note_pagination(content, terminal_height)
            wrapped_lines = pagination_info['wrapped_lines']
            available_content_lines = pagination_info['available_content_lines']
            needs_pagination = pagination_info['needs_pagination']
            total_pages = pagination_info['total_pages']

            max_content_lines = int(available_content_lines * 0.9)
            max_content_lines = max(1, max_content_lines)

            if needs_pagination:
                if page >= total_pages:
                    page = total_pages - 1
                    current_nav['data']['page'] = page
        
                start_idx = page * max_content_lines
                end_idx = start_idx + max_content_lines
                paginated_lines = wrapped_lines[start_idx:end_idx]
                current_page = page + 1
            else:
                if page > 0:
                    page = 0
                    current_nav['data']['page'] = page
                paginated_lines = wrapped_lines
                current_page = 1
                total_pages = 1

            # 🆕 HEADER SHOWS IT'S A HISTORICAL VERSION
            separator = "=" * terminal_width
            print(separator)

            notebook_path = self.manager.get_notebook_hierarchy(notebook.id) if hasattr(notebook, 'id') else []
            if notebook_path:
                path_parts = [nb.name for nb in notebook_path]
                path_str = "/".join(path_parts) + "/"
            else:
                path_str = "Historical/"

            # 🆕 SHOW COMMIT INFO IN HEADER
            commit_hash_short = timeline_data.get('commit_hash', '')[:8]
            header_title = f"{path_str} [HISTORICAL VERSION: {commit_hash_short}]"
            print(f"{header_title:^{terminal_width}}")
            print(separator)

            # NOTE INFO
            is_file_note = hasattr(note, 'file_extension') and note.file_extension is not None

            if is_file_note:
                print(f"File Name: {note.title} [.{note.file_extension} file]")
            else:
                print(f"Note Title: {note.title}")

            # 🆕 SHOW COMMIT DATE INSTEAD OF CURRENT TIMESTAMPS
            commit_date = timeline_data.get('date', datetime.now())
            date_str = commit_date.strftime("%Y-%m-%d %H:%M")
            print(f"Version from: {date_str}")

            print("-" * terminal_width)

            # 🆕 SHOW THE ACTUAL HISTORICAL CONTENT
            for line in paginated_lines:
                print(line)

            if needs_pagination:
                print(f"--- Page {current_page} of {total_pages} ---")
                print()

            # 🆕 TIMELINE-SPECIFIC FOOTER
            print("-" * terminal_width)

            footer_options = ["[V]iew", "[B]ack to timeline"]
    
            if is_file_note:
                footer_options.insert(1, "[X]port")
    
            if needs_pagination:
                if current_page > 1:
                    footer_options.insert(0, "[P]revious")
                if current_page < total_pages:
                    footer_options.insert(0, "[N]ext")

            print("  ".join(footer_options))
            print()

            cmd = self.ui.get_input("> ").strip().lower()

            if cmd == "b":
                self.search_nav_pop()
                break
            elif cmd == "p" and page > 0:
                page -= 1
                self.search_nav_current()['data']['page'] = page
            elif cmd == "n" and current_page < total_pages:
                page += 1
                self.search_nav_current()['data']['page'] = page
            elif cmd == "v":
                try:
                    if is_file_note:
                        self.ui.external_editor(
                            note.content if hasattr(note, 'content') else "", 
                            read_only=True, 
                            file_extension=note.file_extension
                        )
                    else:
                        self.ui.external_editor(
                            note.content if hasattr(note, 'content') else "", 
                            read_only=True
                        )
                except Exception as e:
                    print(f"Error opening editor: {str(e)}")
                    self.ui.get_input("Press Enter to continue...")
            elif cmd == "x" and is_file_note:
                # 🆕 EXPORT HISTORICAL FILE WITH INSTRUCTIONS LIKE REGULAR EXPORT
                self.ui.clear_screen()
                self.ui.print_header(f"Export Historical File: {note.title}")

                print("Enter export DIRECTORY (filename will be automatic):")
                print("Examples:")
                print("  /home/user/projects/")
                print("  ./exports/")
                print("  ../backup/")

                # Show export history if available
                if hasattr(self.ui, 'export_history') and self.ui.export_history:
                    print("\nRecent export paths:")
                    for i, path in enumerate(self.ui.export_history, 1):
                        print(f"[{i}] {path}")
                print()

                print(f"File will be saved as: {note.title}")
                print()

                if hasattr(self.ui, 'export_history') and self.ui.export_history:
                    prompt = "Enter directory or number [1-3]: "
                else:
                    prompt = "Export directory: "

                export_dir = self.ui.get_input(prompt)

                if not export_dir:
                    continue

                # Handle number selection from history
                if export_dir.isdigit() and hasattr(self.ui, 'export_history') and self.ui.export_history:
                    idx = int(export_dir) - 1
                    if 0 <= idx < len(self.ui.export_history):
                        export_dir = self.ui.export_history[idx]
                        print(f"Using: {export_dir}")
                    else:
                        print("Invalid history number.")
                        self.ui.get_input("Press Enter to continue...")
                        continue

                export_dir = os.path.expanduser(export_dir)
                export_path = os.path.join(export_dir, note.title)

                if os.path.exists(export_path) and os.path.isdir(export_path):
                    export_path = os.path.join(export_path, note.title)

                if os.path.isdir(export_path):
                    print(f"Error: '{export_path}' is a directory.")
                    self.ui.get_input("Press Enter to continue...")
                    continue

                if os.path.exists(export_path):
                    confirm = self.ui.get_input(
                        f"File exists. Overwrite '{note.title}'? [y/N]: "
                    )
                    if confirm.lower() != "y":
                        print("Export cancelled.")
                        self.ui.get_input("Press Enter to continue...")
                        continue

                try:
                    os.makedirs(os.path.dirname(export_path), exist_ok=True)
                    with open(export_path, "w", encoding="utf-8") as f:
                        f.write(note.content if hasattr(note, 'content') and note.content else "")
                    print(f"Historical file exported successfully to: {export_path}")

                    # Update export history
                    if hasattr(self.ui, 'export_history'):
                        self.ui._update_export_history(export_dir)

                except Exception as e:
                    print(f"Export failed: {e}")

                self.ui.get_input("Press Enter to continue...")
    
    def clear(self):
        """Clear search cache"""
        self.results = []
        self.query = ""
        self.current_page = 0