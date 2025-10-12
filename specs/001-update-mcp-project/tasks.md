# Tasks: Multi-Environment Configuration Support

**Feature**: 001-update-mcp-project
**Branch**: `001-update-mcp-project`
**Input**: Design documents from `/specs/001-update-mcp-project/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/mcp-tools.md, research.md

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, or SETUP/FOUND for infrastructure)
- Include exact file paths in descriptions

## User Story Organization

- **US1 (P1)**: Switch Between Databricks Environments - MVP 🎯
- **US2 (P2)**: Configure Multiple Environments
- **US3 (P3)**: List and Verify Available Environments

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency management

- [ ] **T001** [SETUP] Update requirements.txt with new production dependencies (watchdog>=3.0.0, pyyaml>=6.0.0)
- [ ] **T002** [P] [SETUP] Update requirements.txt with dev dependencies (pytest>=7.0.0, pytest-mock>=3.10.0)
- [ ] **T003** [P] [SETUP] Create config/ directory and __init__.py
- [ ] **T004** [P] [SETUP] Create models/ directory and __init__.py
- [ ] **T005** [P] [SETUP] Create tools/ directory and __init__.py
- [ ] **T006** [P] [SETUP] Create utils/ directory and __init__.py
- [ ] **T007** [P] [SETUP] Create tests/ directory structure (unit/, integration/, fixtures/) with __init__.py files
- [ ] **T008** [SETUP] Add environments.yaml to .gitignore
- [ ] **T009** [P] [SETUP] Create environments.yaml.template with placeholder values for documentation

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] **T010** [P] [FOUND] Create EnvironmentConfig Pydantic model in models/environment.py with all validators (name, host, token, http_path, description, tags)
- [ ] **T011** [P] [FOUND] Create EnvironmentsConfiguration Pydantic model in models/environment.py with validation (default exists, names match keys)
- [ ] **T012** [P] [FOUND] Create ActiveEnvironment Pydantic model in models/environment.py with get_credentials() and to_summary() methods
- [ ] **T013** [P] [FOUND] Create logging configuration in utils/logger.py with structured formatting for environment operations
- [ ] **T014** [FOUND] Create configuration loader in config/loader.py with load_from_yaml() and load_from_env() functions
- [ ] **T015** [FOUND] Implement EnvironmentManager singleton class in config/manager.py with load_configuration(), set_active_to_default(), and get_active_credentials() methods
- [ ] **T016** [FOUND] Add switch_to_environment(name: str) method to EnvironmentManager with validation and logging
- [ ] **T017** [P] [FOUND] Create configuration validator in config/validator.py with credential completeness checks
- [ ] **T018** [FOUND] Implement backward compatibility logic in config/loader.py to detect and prefer environments.yaml over .env with fallback handling
- [ ] **T019** [P] [FOUND] Create test fixtures in tests/fixtures/ (test_environments.yaml with 2+ envs, test_invalid.yaml, test.env)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Switch Between Databricks Environments (Priority: P1) 🎯 MVP

**Goal**: Enable developers to switch between configured Databricks workspaces and have all MCP tools use the active environment's credentials

**Independent Test**: Configure two environments (dev and prod), switch to each, run a SQL query, and verify correct workspace connection

### Unit Tests for User Story 1

- [ ] **T020** [P] [US1] Write unit test for EnvironmentManager.load_configuration() in tests/unit/test_manager.py (YAML load, .env fallback, error handling)
- [ ] **T021** [P] [US1] Write unit test for EnvironmentManager.switch_to_environment() in tests/unit/test_manager.py (valid switch, invalid environment, validation)
- [ ] **T022** [P] [US1] Write unit test for EnvironmentManager.get_active_credentials() in tests/unit/test_manager.py (returns correct credentials dict)
- [ ] **T023** [P] [US1] Write unit test for configuration loader backward compatibility in tests/unit/test_loader.py (.env detection and implicit config creation)

### Implementation for User Story 1

- [ ] **T024** [US1] Create switch_environment MCP tool in tools/switch_environment.py with validation, error handling, and success message formatting
- [ ] **T025** [P] [US1] Create get_current_environment MCP tool in tools/get_current_environment.py with detailed environment info display
- [ ] **T026** [US1] Modify main.py to initialize EnvironmentManager on startup, load configuration, and set default environment
- [ ] **T027** [US1] Refactor get_databricks_connection() in main.py to read credentials from EnvironmentManager instead of os.getenv()
- [ ] **T028** [US1] Update all existing MCP tools (run_sql_query, list_jobs, get_job_status, get_job_details, create_cluster, delete_cluster, list_clusters, get_cluster_status) to use environment manager credentials with fail-fast error handling
- [ ] **T029** [US1] Register switch_environment and get_current_environment tools in main.py MCP server initialization
- [ ] **T030** [P] [US1] Add logging statements to EnvironmentManager for environment switches (INFO level: "Environment switched: {old} → {new}")
- [ ] **T031** [P] [US1] Add logging for configuration loading (INFO: success, WARNING: fallback to .env, ERROR: no config found)

### Integration Tests for User Story 1

- [ ] **T032** [US1] Write integration test for end-to-end environment switching in tests/integration/test_environment_switching.py (load config, switch environments, verify active environment changes)
- [ ] **T033** [P] [US1] Write integration test for backward compatibility in tests/integration/test_backward_compatibility.py (server starts with .env only, creates implicit config, tools work)
- [ ] **T034** [P] [US1] Write integration test for default environment handling in tests/integration/test_environment_switching.py (server fails to start if no default in multi-env config)

**Checkpoint**: At this point, User Story 1 (MVP) should be fully functional - developers can switch environments and all tools use active credentials

---

## Phase 4: User Story 2 - Configure Multiple Environments (Priority: P2)

**Goal**: Enable developers to define and manage multiple Databricks environments in environments.yaml with validation and auto-reload

**Independent Test**: Create environments.yaml with 3+ environments, load configuration, verify all are accessible, modify file, verify auto-reload

### Unit Tests for User Story 2

- [ ] **T035** [P] [US2] Write unit test for EnvironmentConfig validation in tests/unit/test_validator.py (name validation, host validation, token format, http_path pattern, tags validation)
- [ ] **T036** [P] [US2] Write unit test for EnvironmentsConfiguration validation in tests/unit/test_validator.py (default exists, names match keys, uniqueness)
- [ ] **T037** [P] [US2] Write unit test for config file watcher events in tests/unit/test_watcher.py (file modified event detection, reload trigger)

### Implementation for User Story 2

- [ ] **T038** [US2] Create ConfigWatcher class in config/watcher.py using watchdog.Observer to monitor environments.yaml for changes
- [ ] **T039** [US2] Implement on_modified event handler in ConfigWatcher to trigger configuration reload with validation
- [ ] **T040** [US2] Add validation-before-apply logic in config/watcher.py reload flow (if invalid YAML, keep current config and log error)
- [ ] **T041** [US2] Implement active environment preservation check in reload flow (if active env removed, reset to default with warning log)
- [ ] **T042** [US2] Initialize and start ConfigWatcher in main.py after EnvironmentManager initialization
- [ ] **T043** [P] [US2] Add logging for configuration reload events (WARNING level: "Configuration file changed, reloading: environments.yaml")
- [ ] **T044** [P] [US2] Add logging for reload validation errors (ERROR level with details, keep current config)

### Integration Tests for User Story 2

- [ ] **T045** [US2] Write integration test for file watcher auto-reload in tests/integration/test_environment_switching.py (modify environments.yaml, verify reload, verify new environment available)
- [ ] **T046** [P] [US2] Write integration test for invalid YAML reload in tests/integration/test_environment_switching.py (corrupt file, verify current config preserved, error logged)
- [ ] **T047** [P] [US2] Write integration test for environments.yaml validation in tests/integration/test_environment_switching.py (missing default, duplicate names, invalid credentials)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - environments can be configured in YAML and auto-reload on file changes

---

## Phase 5: User Story 3 - List and Verify Available Environments (Priority: P3)

**Goal**: Provide visibility into configured environments and currently active environment to prevent operational errors

**Independent Test**: Configure 3 environments, select one, list all environments, verify output shows all names with active indicator

### Unit Tests for User Story 3

- [ ] **T048** [P] [US3] Write unit test for list_environments markdown formatting in tests/unit/test_tools.py (table structure, columns, active marker)
- [ ] **T049** [P] [US3] Write unit test for list_environments with no environments in tests/unit/test_tools.py (error message)
- [ ] **T050** [P] [US3] Write unit test for get_current_environment output in tests/unit/test_tools.py (name, host, description, tags, timestamp)

### Implementation for User Story 3

- [ ] **T051** [US3] Create list_environments MCP tool in tools/list_environments.py with markdown table formatting (columns: Environment, Host, Description, Tags, Status)
- [ ] **T052** [US3] Add get_active_environment_name() method to EnvironmentManager for status column in list_environments
- [ ] **T053** [US3] Implement metadata display logic in list_environments (show description and tags if present, N/A if not)
- [ ] **T054** [US3] Register list_environments tool in main.py MCP server initialization
- [ ] **T055** [P] [US3] Add error handling in list_environments for empty configuration (clear message to user)

### Integration Tests for User Story 3

- [ ] **T056** [US3] Write integration test for list_environments display in tests/integration/test_environment_switching.py (list all envs, verify active marker, verify metadata shown)
- [ ] **T057** [P] [US3] Write integration test for get_current_environment after switch in tests/integration/test_environment_switching.py (switch to env, get current, verify match)

**Checkpoint**: All user stories should now be independently functional - complete environment management with visibility

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, security, and quality improvements that affect multiple user stories

- [ ] **T058** [P] [POLISH] Update README.md with multi-environment setup instructions and migration guide from .env
- [ ] **T059** [P] [POLISH] Add security notes to README.md (gitignore, file permissions, never commit credentials)
- [ ] **T060** [POLISH] Verify all logging statements mask credential values (tokens show only first 8 chars)
- [ ] **T061** [P] [POLISH] Add error message quality checks (actionable messages with suggested fixes for all error scenarios)
- [ ] **T062** [P] [POLISH] Run manual validation of quickstart.md scenarios (setup, migration, switching, listing)
- [ ] **T063** [POLISH] Performance validation: verify environment switch < 5s, list < 1s, config reload < 2s
- [ ] **T064** [P] [POLISH] Documentation review: verify quickstart.md examples match actual implementation
- [ ] **T065** [P] [POLISH] Code cleanup: remove any remaining hardcoded environment variable access (search for os.getenv("DATABRICKS_"))

**Final Checkpoint**: Feature complete, documented, and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if team capacity allows)
  - Or sequentially in priority order (P1 → P2 → P3) for single developer
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - MVP)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1/US2 components but independently testable

### Critical Path

```
T001-T009 (Setup)
    ↓
T010-T019 (Foundational) ← BLOCKS EVERYTHING
    ↓
┌───────────┬───────────┬───────────┐
│ T020-T034 │ T035-T047 │ T048-T057 │
│   (US1)   │   (US2)   │   (US3)   │
│   MVP 🎯  │           │           │
└─────┬─────┴─────┬─────┴─────┬─────┘
      │           │           │
      └───────────┴───────────┘
                  ↓
            T058-T065 (Polish)
```

### Within Each User Story

- **Tests before implementation** (Red-Green-Refactor)
- **Models → Services → Tools → Integration**
- **Unit tests → Implementation → Integration tests**
- **Story complete before moving to next priority**

### Parallel Opportunities

**Setup Phase**:
- T002-T007 can all run in parallel (different directories)
- T009 parallel with T008

**Foundational Phase**:
- T010, T011, T012 can run in parallel (different models in same file)
- T013 parallel with T014-T018
- T017 parallel with T014-T016
- T019 parallel with all others (different files)

**User Story 1**:
- T020, T021, T022, T023 tests can all run in parallel (different test files)
- T025 parallel with T024 (different tool files)
- T030, T031 parallel with T024-T029 (different concerns)
- T033, T034 parallel with T032 (different integration test files)

**User Story 2**:
- T035, T036, T037 tests can all run in parallel
- T043, T044 parallel with T038-T042 (logging vs implementation)
- T046, T047 parallel with T045 (different test files)

**User Story 3**:
- T048, T049, T050 tests can all run in parallel
- T055 parallel with T051-T054 (different concern)
- T057 parallel with T056 (different test file)

**Polish Phase**:
- T058, T059, T061, T062, T064, T065 can all run in parallel (different files/concerns)

---

## Parallel Execution Examples

### Example 1: Setup Phase

```bash
# Launch all directory creation tasks together:
parallel --jobs 5 <<EOF
Task T003: Create config/ directory and __init__.py
Task T004: Create models/ directory and __init__.py
Task T005: Create tools/ directory and __init__.py
Task T006: Create utils/ directory and __init__.py
Task T007: Create tests/ directory structure with __init__.py files
EOF
```

### Example 2: Foundational Phase (Models)

```bash
# Launch all Pydantic model tasks together:
parallel --jobs 3 <<EOF
Task T010: Create EnvironmentConfig Pydantic model in models/environment.py
Task T011: Create EnvironmentsConfiguration Pydantic model in models/environment.py
Task T012: Create ActiveEnvironment Pydantic model in models/environment.py
EOF
```

### Example 3: User Story 1 (Tests)

```bash
# Launch all unit tests for US1 together:
parallel --jobs 4 <<EOF
Task T020: Write unit test for EnvironmentManager.load_configuration()
Task T021: Write unit test for EnvironmentManager.switch_to_environment()
Task T022: Write unit test for EnvironmentManager.get_active_credentials()
Task T023: Write unit test for configuration loader backward compatibility
EOF
```

### Example 4: Parallel User Stories (Multi-Developer Team)

With 3 developers after Foundational phase completes:

```
Developer A: Complete all of User Story 1 (T020-T034) → MVP deployed
Developer B: Complete all of User Story 2 (T035-T047) → Auto-reload feature added
Developer C: Complete all of User Story 3 (T048-T057) → Visibility features added
```

Each developer can work independently, test independently, and merge independently.

---

## Implementation Strategy

### Strategy 1: MVP First (Recommended for Single Developer)

**Goal**: Get minimal viable product deployed quickly

1. **Complete Phase 1**: Setup (T001-T009) - ~30 mins
2. **Complete Phase 2**: Foundational (T010-T019) - ~4 hours
3. **Complete Phase 3**: User Story 1 (T020-T034) - ~6 hours
4. **STOP and VALIDATE**:
   - Test environment switching manually
   - Run integration tests
   - Verify backward compatibility with .env
5. **Deploy MVP**: Developers can now switch environments!
6. **Optional**: Add US2 for auto-reload, US3 for visibility

**Total MVP Time**: ~10-11 hours

### Strategy 2: Incremental Delivery

**Goal**: Add value incrementally with each user story

1. **Foundation** (Setup + Foundational) → ~4.5 hours
2. **Add US1** → Test independently → Deploy (MVP!) → ~6 hours
3. **Add US2** → Test independently → Deploy (Auto-reload feature) → ~4 hours
4. **Add US3** → Test independently → Deploy (Visibility features) → ~3 hours
5. **Polish** → Final quality pass → ~2 hours

**Total Time**: ~19.5 hours with full feature set

Each delivery adds value without breaking previous functionality.

### Strategy 3: Parallel Team (3+ Developers)

**Goal**: Maximum speed with team collaboration

1. **Team together**: Setup + Foundational (Phases 1-2) → ~4.5 hours
2. **Split into parallel streams**:
   - **Dev A**: User Story 1 (MVP) → ~6 hours
   - **Dev B**: User Story 2 (Auto-reload) → ~4 hours
   - **Dev C**: User Story 3 (Visibility) → ~3 hours
3. **Team together**: Integration + Polish → ~2 hours

**Total Time**: ~12.5 hours (wall clock with 3 devs)

---

## Task Count Summary

- **Total Tasks**: 65
- **Setup Tasks**: 9
- **Foundational Tasks**: 10
- **User Story 1 (P1 - MVP)**: 15 tasks
- **User Story 2 (P2)**: 13 tasks
- **User Story 3 (P3)**: 10 tasks
- **Polish Tasks**: 8
- **Parallelizable Tasks**: 38 marked with [P]

---

## MVP Scope (Minimum Viable Product)

**Recommended MVP**: Phases 1, 2, and 3 only (Tasks T001-T034)

This delivers:
- ✅ Environment switching capability
- ✅ Active environment tracking
- ✅ Backward compatibility with .env
- ✅ All existing MCP tools work with active environment
- ✅ Error handling and validation
- ✅ Logging for debugging
- ✅ Comprehensive test coverage

**What's deferred** (can add later):
- Auto-reload on file changes (US2)
- Environment listing and verification (US3)

**Why this MVP works**:
- Developers can immediately switch between environments
- Zero breaking changes for existing users
- Independently testable and deployable
- Delivers core value proposition from spec

---

## Notes

- **[P] markers**: Tasks that can run in parallel (different files or independent concerns)
- **[Story] labels**: Map each task to specific user story for traceability and independent testing
- **Checkpoint markers**: Natural stopping points to validate each story works independently
- **Test-first approach**: Unit tests written and failing before implementation begins
- **Commit strategy**: Commit after each logical task or small group of related tasks
- **Error handling**: All tasks include error handling per clarification (fail-fast with clear messages)
- **Logging**: Mask credential values, log at appropriate levels (INFO/WARNING/ERROR)
- **Performance**: Keep targets in mind: <5s switch, <1s list, <2s reload, <1s errors

---

## Validation Checklist

After completing each user story phase:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing confirms independent functionality
- [ ] Logging messages are clear and actionable
- [ ] No credentials exposed in logs
- [ ] Error handling provides clear next steps
- [ ] Performance targets met
- [ ] Backward compatibility maintained
- [ ] Documentation matches implementation
