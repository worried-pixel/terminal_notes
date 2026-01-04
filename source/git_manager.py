# git_manager.py
import os
import subprocess
import uuid
import re
from datetime import datetime
from pathlib import Path


class GitManager:
    def __init__(self, notebook_path):
        self.notebook_path = Path(notebook_path)
        self.repo_initialized = False
        self.current_branch = "master"
        self._check_git_installation()

    def _check_git_installation(self):
        """Check if Git is installed and available"""
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True,
                cwd=self.notebook_path,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fail silently - Git is optional
            pass

    def _run_git_command(self, command, capture_output=True):
        """Run Git command silently"""
        try:
            result = subprocess.run(
                command,
                cwd=self.notebook_path,
                capture_output=capture_output,
                text=True,
                check=True,
            )
            return result
        except subprocess.CalledProcessError:
            return None

    def init_repo(self, notebook_name=None, custom_path=None):
        """Initialize Git repository with smart initial commit"""
        git_dir = self.notebook_path / ".git"
        if not git_dir.exists():
            self._run_git_command(["git", "init"])
            self._run_git_command(["git", "add", "structure.json", "notes.json", "files.json"])
        
            # 🆕 SMART INITIAL COMMIT
            if notebook_name:
                context = "custom location" if custom_path else "default location"
                message = self.generate_commit_message(
                    action="CREATED",
                    content_type="NOTEBOOK", 
                    title=notebook_name,
                    context=context,
                    tags=f"notebook created {notebook_name.lower()}"
                )
            else:
                message = "initial notebook setup"
            
            self._run_git_command(["git", "commit", "-m", message])
            self.repo_initialized = True
        self.repo_initialized = True

    def commit_silently(self, message, files=None):
        """Commit ALL three files always - safe approach"""
        if not self.repo_initialized:
            self.init_repo()

        # 🆕 FIX: ALWAYS commit all three files to be safe
        files = ["structure.json", "notes.json", "files.json"]
    
        for file in files:
            self._run_git_command(["git", "add", file])
    
        result = self._run_git_command(["git", "commit", "-m", message])
        return result is not None
    # 🆕 SMART COMMIT SYSTEM - 8 OPERATIONS

    def generate_commit_message(self, action, content_type, title, context="", description="", tags="", item_uuid=""):
        """Generate structured commit messages for search"""
    
        # Build main message
        message = f"{action} {content_type}: {title}"
        if context:
            message += f" | {context}"
    
        # Add description if provided
        if description:
            message += f"\n\n{description}"
    
        # Add search metadata
        if tags:
            message += f"\n\nMetadata: {tags}"
    
        # 🆕 ADD UUID TO METADATA
        if item_uuid:
            if tags:
                message += f" uuid:{item_uuid}"
            else:
                message += f"\n\nMetadata: uuid:{item_uuid}"
    
        return message

    def detect_note_type(self, note_content, editor_type):
        """Detect if note is quick capture or detailed"""
        word_count = len(note_content.split())
        
        if editor_type == "internal":
            if word_count < 50:
                return "Quick note"
            else:
                return "Text note"
        else:  # vim editor
            if word_count > 200:
                return "Detailed notes"
            else:
                return "Formatted note"

    def detect_file_purpose(self, filename, extension, content):
        """Detect file purpose based on extension and content"""
        purposes = {
            "py": "Python script", "js": "JavaScript code", "html": "Web page",
            "css": "Stylesheet", "md": "Documentation", "json": "Configuration",
            "yml": "YAML config", "yaml": "YAML config", "sh": "Shell script",
            "sql": "Database query", "xml": "XML data", "txt": "Text file",
            "php": "PHP script", "rb": "Ruby script", "java": "Java code",
            "c": "C code", "cpp": "C++ code", "go": "Go code", "rs": "Rust code",
            "pl": "Perl script", "lua": "Lua script", "swift": "Swift code",
            "kt": "Kotlin code", "ts": "TypeScript", "scss": "Sass styles",
            "vue": "Vue component", "jsx": "React component", "bib": "Bibliography",
            "tex": "LaTeX document", "sty": "LaTeX style", "cls": "LaTeX class",
            "toml": "TOML config", "ini": "INI config", "cfg": "Configuration"
        }
        
        return purposes.get(extension, f"{extension.upper()} file")

    def get_content_metrics(self, content):
        """Calculate word count and line count"""
        words = len(content.split())
        lines = len(content.splitlines())
        return words, lines
    # 🎯 8 COMMIT OPERATIONS

    def commit_notebook_creation(self, notebook_uuid, notebook_name, note_count=0, file_count=0, custom_path=None):
        """Commit: CREATE_NOTEBOOK"""
        context = f"{note_count} notes, {file_count} files"
        if custom_path:
            context += f", custom location"
    
        message = self.generate_commit_message(
            action="CREATED",
            content_type="NOTEBOOK", 
            title=notebook_name,
            context=context,
            tags=f"notebook created {notebook_name.lower()}",
            item_uuid=notebook_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, ["structure.json", "notes.json", "files.json"])

    def commit_subnotebook_creation(self, subnotebook_uuid, subnotebook_name, parent_notebook, note_count=0):
        """Commit: CREATE_SUBNOTEBOOK"""
        message = self.generate_commit_message(
            action="CREATED",
            content_type="SUBNOTEBOOK",
            title=subnotebook_name,
            context=f"in {parent_notebook}",
            tags=f"subnotebook created {subnotebook_name.lower()} {parent_notebook.lower()}",
            item_uuid=subnotebook_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, "structure.json")

    def commit_note_creation(self, note_uuid, note_title, notebook_name, editor_type, content=""):
        """Commit: CREATE_NOTE (internal/vim)"""
        note_type = self.detect_note_type(content, editor_type)
        word_count, line_count = self.get_content_metrics(content)
    
        message = self.generate_commit_message(
            action="CREATED",
            content_type="NOTE",
            title=note_title,
            context=f"in {notebook_name} | Editor: {editor_type}, Type: {note_type}",
            description=f"Word count: {word_count} | Lines: {line_count}",
            tags=f"note created {note_title.lower()} {notebook_name.lower()} {editor_type} lines:{line_count}",
            item_uuid=note_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, ["structure.json", "notes.json"])

    def commit_file_creation(self, note_uuid, filename, notebook_name, extension, content=""):
        """Commit: CREATE_FILE"""
        purpose = self.detect_file_purpose(filename, extension, content)
        word_count, line_count = self.get_content_metrics(content)
    
        message = self.generate_commit_message(
            action="CREATED", 
            content_type="FILE",
            title=filename,
            context=f"in {notebook_name} | Type: {purpose}",
            description=f"Lines: {line_count}",
            tags=f"file created {filename} {extension} {notebook_name.lower()} lines:{line_count}",
            item_uuid=note_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, ["structure.json", "files.json"])

    def commit_note_edit(self, note_uuid, note_title, notebook_name, old_content, new_content):
        """Commit: EDIT_CONTENT"""
        old_lines = len(old_content.splitlines())
        new_lines = len(new_content.splitlines())
        line_change = new_lines - old_lines

        old_words = len(old_content.split())
        new_words = len(new_content.split())
        word_change = new_words - old_words

        changes = f"Lines: {old_lines} → {new_lines} ({line_change:+d}) | Words: {old_words} → {new_words} ({word_change:+d})"

        message = self.generate_commit_message(
            action="UPDATED",
            content_type="NOTE",
            title=note_title,
            context=f"in {notebook_name}",
            description=changes,
            tags=f"note edited {note_title.lower()} {notebook_name.lower()} lines:{new_lines} words:{new_words}",
            item_uuid=note_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, ["structure.json", "notes.json"])

    def commit_note_rename(self, note_uuid, old_title, new_title, notebook_name, is_file_note=False):
        """Commit: RENAME_NOTE"""
        content_type = "FILE" if is_file_note else "NOTE"
    
        message = self.generate_commit_message(
            action="RENAMED",
            content_type=content_type,
            title=f"{old_title} → {new_title}",
            context=f"in {notebook_name}",
            tags=f"renamed {old_title.lower()} {new_title.lower()} {notebook_name.lower()}",
            item_uuid=note_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, "structure.json")

    def commit_note_deletion(self, note_uuid, note_title, notebook_name, is_file_note=False):
        """Commit: DELETE_NOTE"""
        content_type = "FILE" if is_file_note else "NOTE"
    
        message = self.generate_commit_message(
            action="DELETED",
            content_type=content_type,
            title=note_title,
            context=f"from {notebook_name}",
            tags=f"deleted {note_title.lower()} {notebook_name.lower()}",
            item_uuid=note_uuid  # 🆕 ADD UUID
        )
        if is_file_note:
            return self.commit_silently(message, ["structure.json", "files.json"])
        else:
            return self.commit_silently(message, ["structure.json", "notes.json"])

    def commit_subnotebook_deletion(self, subnotebook_uuid, subnotebook_name, parent_notebook):
        """Commit: DELETE_SUBNOTEBOOK"""
        message = self.generate_commit_message(
            action="DELETED",
            content_type="SUBNOTEBOOK",
            title=subnotebook_name,
            context=f"from {parent_notebook}",
            tags=f"subnotebook deleted {subnotebook_name.lower()} {parent_notebook.lower()}",
            item_uuid=subnotebook_uuid  # 🆕 ADD UUID
        )
        return self.commit_silently(message, "structure.json")