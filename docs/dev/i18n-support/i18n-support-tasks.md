# 任务清单: i18n Support

> **Feature**: i18n-support
> **Base Branch**: feature/dev

## Phase 1: Infrastructure & Refactoring

- [ ] **Task-001**: Create LanguageManager class
  - Implement loading/saving logic
  - Handle QTranslator installation
  - Define translation file paths (handling frozen/dev env)
  - **Files**: `src/docx_server_launcher/core/language_manager.py`

- [ ] **Task-002**: Refactor MainWindow for Dynamic Translation
  - Wrap all user-visible strings with `self.tr()`
  - Move text assignment to `retranslateUi()` method
  - Implement `changeEvent` handler
  - **Files**: `src/docx_server_launcher/gui/main_window.py`

## Phase 2: Translation Implementation

- [ ] **Task-003**: Generate Translation Files
  - Setup script to run `pylupdate6`
  - Create `zh_CN.ts`
  - Perform translation (Chinese)
  - Compile to `zh_CN.qm`
  - **Files**: `scripts/update_translations.sh`, `src/docx_server_launcher/resources/translations/`

- [ ] **Task-004**: Integrate Language Selector
  - Add ComboBox to MainWindow (in Config section or Menu)
  - Connect to LanguageManager
  - Sync UI state with current language
  - **Files**: `src/docx_server_launcher/gui/main_window.py`

## Phase 3: Build & Release

- [ ] **Task-005**: Update Build Configuration
  - Modify `.spec` file to include translation directory
  - Update `build_exe.ps1` / `build_exe.sh` if needed to compile translations before build
  - **Files**: `docx-server-launcher.spec`, `scripts/build_exe.ps1`
