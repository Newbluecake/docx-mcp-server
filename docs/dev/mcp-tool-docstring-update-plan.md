# MCP Tool Docstring Update Plan

## Overview

**Goal**: Optimize all 57 MCP tool docstrings to help Claude AI understand:
- How to obtain and use session_id
- Active file concept and session management
- Complete workflows from start to finish
- How to parse Markdown responses

**Status**: In Progress
**Started**: 2026-01-27
**Guidelines**: See `mcp-tool-docstring-guidelines.md`

## Progress Tracking

### Phase 1: High Priority (Core Workflow) - 28 tools

#### session_tools.py (6 tools) - ✅ MOSTLY COMPLETE
- [x] docx_create - Excellent docstring with v3.0 migration guide
- [x] docx_close - Good docstring with examples
- [x] docx_save - Good docstring with examples
- [x] docx_get_context - Good docstring
- [ ] docx_list_sessions - **NEEDS UPDATE** (minimal docstring)
- [ ] docx_cleanup_sessions - **NEEDS UPDATE** (minimal docstring)

**Priority**: Update docx_list_sessions and docx_cleanup_sessions

#### paragraph_tools.py (6 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_insert_paragraph - **NEEDS UPDATE** (missing workflow examples)
- [ ] docx_insert_heading - **NEEDS UPDATE** (minimal docstring)
- [ ] docx_update_paragraph_text - **NEEDS UPDATE**
- [ ] docx_copy_paragraph - **NEEDS UPDATE**
- [ ] docx_delete - **NEEDS UPDATE**
- [ ] docx_insert_page_break - **NEEDS UPDATE**

**Priority**: HIGH - These are core document building tools

#### content_tools.py (3 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_read_content - **NEEDS UPDATE** (good but missing session context block)
- [ ] docx_find_paragraphs - **NEEDS UPDATE**
- [ ] docx_extract_template_structure - **NEEDS UPDATE**

**Priority**: HIGH - Essential for reading and searching documents

#### table_tools.py (11 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_insert_table - **NEEDS UPDATE**
- [ ] docx_get_table - **NEEDS UPDATE**
- [ ] docx_list_tables - **NEEDS UPDATE**
- [ ] docx_find_table - **NEEDS UPDATE**
- [ ] docx_get_cell - **NEEDS UPDATE**
- [ ] docx_insert_paragraph_to_cell - **NEEDS UPDATE**
- [ ] docx_insert_table_row - **NEEDS UPDATE**
- [ ] docx_insert_table_col - **NEEDS UPDATE**
- [ ] docx_fill_table - **NEEDS UPDATE**
- [ ] docx_copy_table - **NEEDS UPDATE**
- [ ] docx_get_table_structure - **NEEDS UPDATE**

**Priority**: HIGH - Tables are frequently used

#### composite_tools.py (5 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_insert_formatted_paragraph - **NEEDS UPDATE**
- [ ] docx_quick_edit - **NEEDS UPDATE**
- [ ] docx_get_structure_summary - **NEEDS UPDATE**
- [ ] docx_smart_fill_table - **NEEDS UPDATE**
- [ ] docx_format_range - **NEEDS UPDATE**

**Priority**: HIGH - These are high-level convenience tools

### Phase 2: Medium Priority (Frequently Used) - 15 tools

#### run_tools.py (3 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_insert_run - **NEEDS UPDATE**
- [ ] docx_update_run_text - **NEEDS UPDATE**
- [ ] docx_set_font - **NEEDS UPDATE**

#### format_tools.py (6 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_set_alignment - **NEEDS UPDATE**
- [ ] docx_set_properties - **NEEDS UPDATE**
- [ ] docx_format_copy - **NEEDS UPDATE**
- [ ] docx_set_margins - **NEEDS UPDATE**
- [ ] docx_extract_format_template - **NEEDS UPDATE**
- [ ] docx_apply_format_template - **NEEDS UPDATE**

#### advanced_tools.py (3 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_replace_text - **NEEDS UPDATE**
- [ ] docx_batch_replace_text - **NEEDS UPDATE**
- [ ] docx_insert_image - **NEEDS UPDATE**

#### history_tools.py (3 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_log - **NEEDS UPDATE**
- [ ] docx_rollback - **NEEDS UPDATE**
- [ ] docx_checkout - **NEEDS UPDATE**

### Phase 3: Low Priority (Specialized) - 14 tools

#### cursor_tools.py (2 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_cursor_get - **NEEDS UPDATE**
- [ ] docx_cursor_move - **NEEDS UPDATE**

#### copy_tools.py (2 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_get_element_source - **NEEDS UPDATE**
- [ ] docx_copy_elements_range - **NEEDS UPDATE**

#### system_tools.py (3 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_server_status - **NEEDS UPDATE**
- [ ] docx_get_log_level - **NEEDS UPDATE**
- [ ] docx_set_log_level - **NEEDS UPDATE**

#### table_rowcol_tools.py (4 tools) - 🔄 NEEDS IMPROVEMENT
- [ ] docx_insert_row_at - **NEEDS UPDATE**
- [ ] docx_insert_col_at - **NEEDS UPDATE**
- [ ] docx_delete_row - **NEEDS UPDATE**
- [ ] docx_delete_col - **NEEDS UPDATE**

## Update Strategy

### Batch Processing
Update tools in batches by module to maintain consistency:

1. **Batch 1**: session_tools.py (2 tools remaining)
2. **Batch 2**: paragraph_tools.py (6 tools)
3. **Batch 3**: content_tools.py (3 tools)
4. **Batch 4**: table_tools.py (11 tools)
5. **Batch 5**: composite_tools.py (5 tools)
6. **Batch 6**: run_tools.py + format_tools.py (9 tools)
7. **Batch 7**: advanced_tools.py + history_tools.py (6 tools)
8. **Batch 8**: Remaining specialized tools (12 tools)

### Quality Checks
For each updated tool, verify:
- [ ] Session Context block present (if session_id required)
- [ ] Standard session_id description used
- [ ] Examples include complete workflow
- [ ] Element ID extraction example (if applicable)
- [ ] See Also section links docx_create
- [ ] Migration notes (if breaking change)
- [ ] Markdown response format documented

## Estimated Impact

**Total tools**: 57
**Tools needing updates**: ~53 (93%)
**Tools with good docstrings**: 4 (7%)

**Expected benefits**:
1. Claude AI will better understand session management
2. Reduced errors from incorrect tool usage
3. Better workflow understanding (create → operate → save → close)
4. Clearer active file concept
5. Improved response parsing (Markdown format)

## Next Steps

1. ✅ Create guidelines document
2. ✅ Create update plan
3. 🔄 Start with Batch 1: Complete session_tools.py
4. ⏳ Continue with Batch 2-8
5. ⏳ Test updated docstrings with Claude AI
6. ⏳ Update CLAUDE.md with new examples
