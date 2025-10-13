# AI Assistant Documentation System

**Version**: 3.0
**Last Updated**: 2025-10-13
**Managed by**: Orchestrator Agent

---

## 🗺️ Documentation Navigation

**Start Here**: [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) - Complete documentation structure with visual diagrams

---

## 📚 Quick Access by Category

### 1. 🎯 Core Project Documents
```
📄 Claude.md (ROOT)           → Project rules & standards
📄 README.md (ROOT)           → Project overview
📄 DOCUMENTATION_MAP.md       → Full documentation map & navigation
```

### 2. 🏗️ Architecture (System Design)
```
docs/architecture/
├── 📄 README.md                           → Architecture documentation index
├── 📄 ARCHITECTURE_OVERVIEW.md            → High-level system architecture
├── 📄 MULTI_AGENT_SYSTEM_ARCHITECTURE.md  → Multi-agent collaboration design
├── 📄 DATA_AGENT_ARCHITECTURE.md          → Data Agent detailed design
├── 📄 STRATEGY_AGENT_ARCHITECTURE.md      → Strategy Agent detailed design
├── 📄 HELPER_AGENT_ARCHITECTURE.md        → Helper Agent detailed design
├── 📄 SERVICE_LAYER_BACKTEST_ARCHITECTURE.md → Backtest system architecture
└── 📄 DATABASE_ARCHITECTURE.md            → MongoDB database structure
```

**Purpose**: Understand **WHAT** the system does and **WHY** design decisions were made

### 3. 🔌 Interfaces (Component Contracts)
```
docs/interfaces/
├── 📄 AGENT_INTERFACES.md              → Agent-to-agent RPC communication
├── 📄 INTERFACE_SPECIFICATION.md       → Data structure formats (DataFrame/Dict)
├── 📄 DATA_LAYER_INTERFACES.md         → Column specs (DB→Indicator→Strategy)
│
├── 📄 DATABASE_LAYER_INTERFACE.md      → MongoDB CRUD operations
├── 📄 INDICATOR_LAYER_INTERFACE.md     → Technical indicator calculations
├── 📄 STRATEGY_LAYER_INTERFACE.md      → Signal generation methods
├── 📄 SERVICE_LAYER_INTERFACE.md       → Backtest & execution services
└── 📄 HELPER_LAYER_INTERFACE.md        → External API integrations
```

**Purpose**: Define **HOW** components interact with each other

**Key Documents**:
- **AGENT_INTERFACES.md**: How agents communicate (messages, protocols)
- **INTERFACE_SPECIFICATION.md**: Data formats between layers
- **DATA_LAYER_INTERFACES.md**: Column specifications (refer to JSON files)

### 4. 📋 Specifications (Implementation Details)
```
docs/specs/
├── 📄 API_INTEGRATION_SPEC.md          → External API specifications
├── 📄 BACKTEST_SERVICE_SPEC.md         → Backtest engine detailed specs
├── 📄 DATABASE_SCHEMA.md               → MongoDB schema definitions
├── 📄 SIGNAL_GENERATION_SPEC.md        → Signal logic specifications
├── 📄 TECHNICAL_INDICATORS_SPEC.md     → Indicator calculation formulas
├── 📄 README_EXECUTION_MODULES.md      → Execution module specs
│
├── 📁 data_usage/
│   └── 📄 BACKTEST_VS_TRADING_DATA_USAGE.md → T-1 vs T data timing rules
│
└── 📁 implementation/
    └── 📄 IMPLEMENTATION_SUMMARY.md     → Implementation details & summaries
```

**Purpose**: Describe **EXACTLY HOW** to implement features

### 5. 🎨 Features (End-to-End Feature Documentation)
```
docs/features/
├── 📄 SIGNAL_TIMELINE_FEATURE.md       → Individual ticker signal timeline
├── 📄 SIGNAL_CONFIG_GUIDE.md           → Signal configuration system
├── 📄 HYBRID_MODEL_GUIDE.md            → Multiple LLM model usage
├── 📄 INTERACTIVE_ORCHESTRATOR_GUIDE.md → Interactive orchestrator
└── 📄 REQUEST_TYPE_SYSTEM.md           → Request classification system
```

**Purpose**: Complete feature documentation from user perspective

### 6. 🔧 Modules (API References)
```
docs/modules/
├── 📄 DATABASE_MODULES.md              → Database module API reference
├── 📄 INDICATOR_MODULES.md             → Indicator module API reference
├── 📄 STRATEGY_MODULES.md              → Strategy module API reference
├── 📄 SERVICE_MODULES.md               → Service module API reference
└── 📄 HELPER_MODULES.md                → Helper module API reference
```

**Purpose**: Specific function APIs and code examples

### 7. 📚 Functions (Function Manuals)
```
docs/functions/
├── 📄 DATA_AGENT_FUNCTIONS.md          → Data Agent function catalog
└── 📄 HELPER_FUNCTIONS_MANUAL.md       → Helper Agent function catalog
```

**Purpose**: Comprehensive function lists with usage examples

### 8. 👥 User Guides (End-User Documentation)
```
docs/user_guides/
├── 📄 USER_MANUAL_KOREAN.md            → Complete user manual (Korean)
├── 📄 QUICK_START_TRADING.md           → Quick start guide
├── 📄 사용_가이드.md                    → Usage guide (Korean)
└── 📄 터미널_실행_가이드.md              → Terminal execution guide (Korean)
```

**Purpose**: Help end-users operate the system

### 9. 🔐 Management (System Administration)
```
docs/management/
├── 📄 FILE_PERMISSIONS.md              → File access control matrix
├── 📄 AGENT_LAYER_OWNERSHIP.md         → Layer ownership rules
├── 📄 LAYER_DOCUMENTATION_GUIDE.md     → Documentation standards
└── 📄 MIGRATION_GUIDE.md               → System migration procedures
```

**Purpose**: System management and governance

### 10. 🚀 Orchestrator (Orchestrator System)
```
docs/orchestrator/
└── 📄 README.md                        → Orchestrator documentation
```

**Purpose**: Orchestrator-specific documentation

---

## 🎯 Navigation by Role

### For New Developers
```
1. Claude.md (ROOT) → Understand project rules
2. docs/DOCUMENTATION_MAP.md → See full documentation structure
3. docs/architecture/ARCHITECTURE_OVERVIEW.md → Understand system design
4. docs/interfaces/AGENT_INTERFACES.md → Learn agent communication
5. Dive into specific agent architecture docs
```

### For Agent Developers
```
Agent-Specific Flow:

1. docs/architecture/[AGENT]_ARCHITECTURE.md
   ↓
2. docs/interfaces/[LAYER]_INTERFACE.md
   ↓
3. docs/modules/[LAYER]_MODULES.md
   ↓
4. docs/functions/[AGENT]_FUNCTIONS.md (if exists)
```

**Example - Data Agent Developer**:
```
START → architecture/DATA_AGENT_ARCHITECTURE.md
  ↓
interfaces/DATABASE_LAYER_INTERFACE.md (MongoDB operations)
  ↓
interfaces/INDICATOR_LAYER_INTERFACE.md (Technical indicators)
  ↓
interfaces/DATA_LAYER_INTERFACES.md (Column specifications)
  ↓
modules/DATABASE_MODULES.md & modules/INDICATOR_MODULES.md
  ↓
functions/DATA_AGENT_FUNCTIONS.md
  ↓
specs/DATABASE_SCHEMA.md & specs/TECHNICAL_INDICATORS_SPEC.md
```

### For Feature Developers
```
1. Identify which agent(s) involved
2. Read related architecture docs
3. Check interface specs
4. Create feature doc in docs/features/
5. Update DOCUMENTATION_MAP.md
```

### For System Operators
```
1. user_guides/USER_MANUAL_KOREAN.md
2. user_guides/QUICK_START_TRADING.md
3. management/FILE_PERMISSIONS.md (if admin access needed)
```

---

## 🔍 Document Lookup by Task

| **Task** | **Primary Document** | **Related Documents** |
|----------|---------------------|----------------------|
| **Understand system** | `architecture/ARCHITECTURE_OVERVIEW.md` | `MULTI_AGENT_SYSTEM_ARCHITECTURE.md` |
| **Add new agent** | `architecture/MULTI_AGENT_SYSTEM_ARCHITECTURE.md` | `interfaces/AGENT_INTERFACES.md` |
| **Modify data flow** | `interfaces/DATA_LAYER_INTERFACES.md` | `INTERFACE_SPECIFICATION.md` |
| **Add indicator** | `interfaces/INDICATOR_LAYER_INTERFACE.md` | `specs/TECHNICAL_INDICATORS_SPEC.md` |
| **Change signal logic** | `interfaces/STRATEGY_LAYER_INTERFACE.md` | `specs/SIGNAL_GENERATION_SPEC.md` |
| **Modify backtest** | `architecture/SERVICE_LAYER_BACKTEST_ARCHITECTURE.md` | `specs/BACKTEST_SERVICE_SPEC.md` |
| **Add external API** | `interfaces/HELPER_LAYER_INTERFACE.md` | `specs/API_INTEGRATION_SPEC.md` |
| **Debug data issues** | `interfaces/DATA_LAYER_INTERFACES.md` | `specs/DATABASE_SCHEMA.md` |
| **Add feature** | Create in `features/` | Depends on feature type |
| **User support** | `user_guides/USER_MANUAL_KOREAN.md` | `user_guides/QUICK_START_TRADING.md` |

---

## 📊 Core Document Relationships

```
┌─────────────────────────────────────────────────────────┐
│                 Claude.md (Project Rules)               │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
  │ Architecture │ │ Interfaces  │ │    Specs     │
  │   (Design)   │ │ (Contracts) │ │  (Details)   │
  └──────────────┘ └─────────────┘ └──────────────┘
          │               │               │
          └───────┬───────┴───────┬───────┘
                  │               │
          ┌───────▼───────┐ ┌────▼────┐
          │    Modules    │ │Features │
          │  (Functions)  │ │  (E2E)  │
          └───────────────┘ └─────────┘
                  │
          ┌───────▼──────────┐
          │   User Guides    │
          │  (End-Users)     │
          └──────────────────┘
```

### Document Hierarchy
1. **Claude.md**: Project rules (highest authority)
2. **Architecture**: System design decisions
3. **Interfaces**: Component contracts
4. **Specifications**: Implementation details
5. **Modules**: Code-level APIs
6. **Features**: User-facing features
7. **User Guides**: End-user documentation

---

## 📝 Key Conventions

### Core Interface Documents
These 3 documents define **ALL** system interactions:

1. **AGENT_INTERFACES.md** (`docs/interfaces/`)
   - How agents communicate (RPC, messages)
   - Request/Response formats
   - Error handling protocols

2. **INTERFACE_SPECIFICATION.md** (`docs/interfaces/`)
   - Data structure formats (DataFrame, Dict)
   - Indicator→Strategy data format
   - Strategy output format (df_dump, Universe)

3. **DATA_LAYER_INTERFACES.md** (`docs/interfaces/`)
   - Column specifications
   - Market DB → Indicator Layer
   - Indicator Layer → Strategy Layer
   - References JSON files in `refer/debug_json/`

### Architecture Documents
**Read these first** to understand system design:
- `architecture/ARCHITECTURE_OVERVIEW.md` - Start here
- `architecture/MULTI_AGENT_SYSTEM_ARCHITECTURE.md` - Agent collaboration
- Agent-specific architecture docs for detailed design

### Module Documents
**Use these for coding**:
- API references with function signatures
- Code examples
- Parameter descriptions

---

## 🔄 Documentation Update Rules

### When to Update Documentation

| **Code Change** | **Must Update** | **Consider Updating** |
|----------------|-----------------|----------------------|
| New function | Module docs | Interface docs |
| New agent | Architecture, Interface, Module docs | DOCUMENTATION_MAP |
| Data structure change | INTERFACE_SPECIFICATION, DATA_LAYER_INTERFACES | Related module docs |
| New column | DATA_LAYER_INTERFACES, JSON files | Module docs |
| Signal logic change | SIGNAL_GENERATION_SPEC, STRATEGY_LAYER_INTERFACE | Module docs |
| New feature | Create feature doc, Update README | Update DOCUMENTATION_MAP |
| API endpoint change | API_INTEGRATION_SPEC, HELPER_LAYER_INTERFACE | Module docs |

### Documentation Standards
- **Version**: Include version number
- **Last Updated**: Include date (YYYY-MM-DD)
- **Managed by**: Specify responsible agent
- **Related Documentation**: Link to related docs
- **Code Examples**: Always provide working examples
- **Cross-References**: Use relative paths

---

## 🎯 Document Status

| Category | Document Count | Status |
|----------|----------------|--------|
| Architecture | 8 | ✅ Complete |
| Interfaces | 8 | ✅ Complete |
| Specifications | 8 | ✅ Complete |
| Features | 5 | ✅ Complete |
| Modules | 5 | ✅ Complete |
| Functions | 2 | ⚠️ Partial (Strategy/Service TBD) |
| User Guides | 4 | ✅ Complete |
| Management | 4 | ✅ Complete |

**Total Documents**: 50

---

## 🔗 External Resources

- **refer/debug_json/**: Column specification JSON files
  - `df_*_columns_before_TRD.json` (Market DB output)
  - `df_*_columns_after_TRD.json` (Indicator Layer output)

- **config/**: Configuration files
  - `myStockInfo.yaml` - Main configuration
  - `signal_config.yaml` - Signal configuration
  - `agent_model.yaml` - LLM model assignments

- **project/**: Source code
  - Inline documentation in Python files
  - Type hints and docstrings

---

## 🚀 Getting Started

### First Time Here?
1. Read `Claude.md` (ROOT) - Project rules
2. Read `DOCUMENTATION_MAP.md` - Full navigation
3. Read `architecture/ARCHITECTURE_OVERVIEW.md` - System overview
4. Choose your role path above

### Need Quick Answer?
- Check the "Document Lookup by Task" table above
- Use `DOCUMENTATION_MAP.md` for detailed navigation

### Adding New Documentation?
1. Determine category (Architecture/Interface/Spec/etc.)
2. Follow documentation standards (version, date, links)
3. Update `DOCUMENTATION_MAP.md`
4. Update this `README.md` if major change

---

## 📞 Support

- **Documentation Issues**: Check `DOCUMENTATION_MAP.md` first
- **Code Questions**: Check module and function docs
- **Feature Requests**: Check `features/` folder
- **System Administration**: Check `management/` folder

---

**Maintained by**: Orchestrator Agent
**Update Frequency**: On major structural changes
**Last Review**: 2025-10-13

---

## Quick Links

- 🗺️ [Complete Documentation Map](DOCUMENTATION_MAP.md)
- 📐 [System Architecture](architecture/ARCHITECTURE_OVERVIEW.md)
- 🔌 [Agent Communication](interfaces/AGENT_INTERFACES.md)
- 📊 [Data Interfaces](interfaces/DATA_LAYER_INTERFACES.md)
- 👤 [User Manual](user_guides/USER_MANUAL_KOREAN.md)
