# Documentation Structure Map

**Version**: 3.0
**Last Updated**: 2025-10-13
**Purpose**: Central navigation hub for all project documentation

---

## 📚 Documentation Categories

### 1. 🎯 Core Project Rules
```
Claude.md (ROOT)           → Project-wide rules and standards
README.md (ROOT)           → Project overview
```

### 2. 🏗️ Architecture Documentation
```
docs/architecture/
├── README.md                           → Architecture index
├── ARCHITECTURE_OVERVIEW.md            → System overview
├── MULTI_AGENT_SYSTEM_ARCHITECTURE.md  → Multi-agent design
├── DATA_AGENT_ARCHITECTURE.md          → Data Agent design
├── STRATEGY_AGENT_ARCHITECTURE.md      → Strategy Agent design
├── HELPER_AGENT_ARCHITECTURE.md        → Helper Agent design
├── SERVICE_LAYER_BACKTEST_ARCHITECTURE.md → Backtest system
└── DATABASE_ARCHITECTURE.md            → MongoDB structure
```

### 3. 🔌 Interface Specifications
```
docs/interfaces/
├── AGENT_INTERFACES.md              → Agent-to-agent communication (RPC)
├── INTERFACE_SPECIFICATION.md       → Data structure formats (DataFrame)
├── DATA_LAYER_INTERFACES.md         → Column specs (DB→Indicator→Strategy)
│
├── DATABASE_LAYER_INTERFACE.md      → Database CRUD operations
├── INDICATOR_LAYER_INTERFACE.md     → Technical indicator calculations
├── STRATEGY_LAYER_INTERFACE.md      → Signal generation methods
├── SERVICE_LAYER_INTERFACE.md       → Backtest & execution services
└── HELPER_LAYER_INTERFACE.md        → External API integrations
```

### 4. 📋 Technical Specifications
```
docs/specs/
├── API_INTEGRATION_SPEC.md          → External API specs
├── BACKTEST_SERVICE_SPEC.md         → Backtest engine specs
├── DATABASE_SCHEMA.md               → MongoDB schema
├── SIGNAL_GENERATION_SPEC.md        → Signal logic specs
├── TECHNICAL_INDICATORS_SPEC.md     → Indicator formulas
├── README_EXECUTION_MODULES.md      → Execution modules
│
├── data_usage/
│   └── BACKTEST_VS_TRADING_DATA_USAGE.md → Data timing rules
│
└── implementation/
    └── IMPLEMENTATION_SUMMARY.md     → Implementation details
```

### 5. 📖 Feature Documentation
```
docs/features/
├── SIGNAL_TIMELINE_FEATURE.md       → Signal timeline visualization
├── SIGNAL_CONFIG_GUIDE.md           → Signal configuration
├── HYBRID_MODEL_GUIDE.md            → Hybrid LLM model usage
├── INTERACTIVE_ORCHESTRATOR_GUIDE.md → Interactive orchestrator
└── REQUEST_TYPE_SYSTEM.md           → Request classification system
```

### 6. 🔧 Module Documentation
```
docs/modules/
├── DATABASE_MODULES.md              → Database module APIs
├── INDICATOR_MODULES.md             → Indicator module APIs
├── STRATEGY_MODULES.md              → Strategy module APIs
├── SERVICE_MODULES.md               → Service module APIs
└── HELPER_MODULES.md                → Helper module APIs
```

### 7. 📚 Agent Function Manuals
```
docs/functions/
├── DATA_AGENT_FUNCTIONS.md          → Data Agent function list
├── HELPER_FUNCTIONS_MANUAL.md       → Helper Agent function list
└── [Future: STRATEGY_AGENT_FUNCTIONS.md]
```

### 8. 👥 User Guides
```
docs/user_guides/
├── USER_MANUAL_KOREAN.md            → Complete user manual (Korean)
├── QUICK_START_TRADING.md           → Quick start guide
├── 사용_가이드.md                    → Usage guide (Korean)
└── 터미널_실행_가이드.md              → Terminal execution guide (Korean)
```

### 9. 🔐 System Management
```
docs/management/
├── FILE_PERMISSIONS.md              → File access control
├── AGENT_LAYER_OWNERSHIP.md         → Layer ownership rules
├── LAYER_DOCUMENTATION_GUIDE.md     → Documentation standards
└── MIGRATION_GUIDE.md               → Migration procedures
```

### 10. 🚀 Orchestrator Documentation
```
docs/orchestrator/
└── README.md                        → Orchestrator system guide
```

---

## 🗺️ Documentation Flow by Agent

### 📊 Data Agent Documentation Flow
```
START: architecture/DATA_AGENT_ARCHITECTURE.md
  ↓
interfaces/DATABASE_LAYER_INTERFACE.md (MongoDB CRUD)
  ↓
interfaces/INDICATOR_LAYER_INTERFACE.md (Technical indicators)
  ↓
DATA_LAYER_INTERFACES.md (Column specifications)
  ↓
modules/DATABASE_MODULES.md & modules/INDICATOR_MODULES.md
  ↓
functions/DATA_AGENT_FUNCTIONS.md
  ↓
specs/DATABASE_SCHEMA.md & specs/TECHNICAL_INDICATORS_SPEC.md
```

### 🎯 Strategy Agent Documentation Flow
```
START: architecture/STRATEGY_AGENT_ARCHITECTURE.md
  ↓
interfaces/STRATEGY_LAYER_INTERFACE.md (Signal generation)
  ↓
INTERFACE_SPECIFICATION.md (Strategy output format)
  ↓
modules/STRATEGY_MODULES.md
  ↓
specs/SIGNAL_GENERATION_SPEC.md
  ↓
features/SIGNAL_CONFIG_GUIDE.md
  ↓
specs/data_usage/BACKTEST_VS_TRADING_DATA_USAGE.md
```

### ⚙️ Service Agent Documentation Flow
```
START: architecture/SERVICE_LAYER_BACKTEST_ARCHITECTURE.md
  ↓
interfaces/SERVICE_LAYER_INTERFACE.md (Backtest & execution)
  ↓
modules/SERVICE_MODULES.md
  ↓
specs/BACKTEST_SERVICE_SPEC.md
  ↓
specs/README_EXECUTION_MODULES.md
```

### 🔧 Helper Agent Documentation Flow
```
START: architecture/HELPER_AGENT_ARCHITECTURE.md
  ↓
interfaces/HELPER_LAYER_INTERFACE.md (External APIs)
  ↓
modules/HELPER_MODULES.md
  ↓
functions/HELPER_FUNCTIONS_MANUAL.md
  ↓
specs/API_INTEGRATION_SPEC.md
```

### 🎛️ Orchestrator Agent Documentation Flow
```
START: architecture/MULTI_AGENT_SYSTEM_ARCHITECTURE.md
  ↓
orchestrator/README.md
  ↓
AGENT_INTERFACES.md (Agent communication)
  ↓
features/INTERACTIVE_ORCHESTRATOR_GUIDE.md
  ↓
features/HYBRID_MODEL_GUIDE.md
  ↓
features/REQUEST_TYPE_SYSTEM.md
```

---

## 📊 Visual Documentation Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude.md (ROOT)                         │
│                   Project Rules & Standards                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
    ┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
    │  Architecture    │ │  Interfaces  │ │  Specifications │
    │  (Design)        │ │  (Contracts) │ │  (Details)      │
    └──────────────────┘ └──────────────┘ └─────────────────┘
            │                    │                  │
            │                    │                  │
    ┌───────┴────────┐   ┌───────┴────────┐ ┌──────┴────────┐
    │                │   │                │ │               │
    ▼                ▼   ▼                ▼ ▼               ▼
┌────────┐     ┌────────┐ ┌──────────┐ ┌────────┐    ┌──────────┐
│ Data   │     │Strategy│ │ Service  │ │ Helper │    │ Features │
│ Agent  │     │ Agent  │ │ Agent    │ │ Agent  │    │ Docs     │
└────────┘     └────────┘ └──────────┘ └────────┘    └──────────┘
    │              │           │            │              │
    ▼              ▼           ▼            ▼              ▼
┌────────────────────────────────────────────────────────────────┐
│                    Module Documentation                         │
│        (API References, Function Lists, Code Examples)          │
└────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                    User Guides & Manuals                        │
│           (End-user documentation, Quick starts)                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Document Lookup by Task

| **Task** | **Primary Document** | **Related Documents** |
|----------|---------------------|----------------------|
| **Add new agent** | `architecture/MULTI_AGENT_SYSTEM_ARCHITECTURE.md` | `AGENT_INTERFACES.md`, `LAYER_DOCUMENTATION_GUIDE.md` |
| **Modify data flow** | `DATA_LAYER_INTERFACES.md` | `INTERFACE_SPECIFICATION.md`, `DATABASE_LAYER_INTERFACE.md` |
| **Add technical indicator** | `interfaces/INDICATOR_LAYER_INTERFACE.md` | `specs/TECHNICAL_INDICATORS_SPEC.md`, `modules/INDICATOR_MODULES.md` |
| **Change signal logic** | `interfaces/STRATEGY_LAYER_INTERFACE.md` | `specs/SIGNAL_GENERATION_SPEC.md`, `features/SIGNAL_CONFIG_GUIDE.md` |
| **Modify backtest** | `architecture/SERVICE_LAYER_BACKTEST_ARCHITECTURE.md` | `specs/BACKTEST_SERVICE_SPEC.md`, `specs/data_usage/BACKTEST_VS_TRADING_DATA_USAGE.md` |
| **Add external API** | `interfaces/HELPER_LAYER_INTERFACE.md` | `specs/API_INTEGRATION_SPEC.md`, `functions/HELPER_FUNCTIONS_MANUAL.md` |
| **Debug data issues** | `DATA_LAYER_INTERFACES.md` | `specs/DATABASE_SCHEMA.md`, `architecture/DATABASE_ARCHITECTURE.md` |
| **Add new feature** | `features/` | Depends on feature type |
| **User onboarding** | `user_guides/USER_MANUAL_KOREAN.md` | `user_guides/QUICK_START_TRADING.md` |
| **System architecture** | `architecture/ARCHITECTURE_OVERVIEW.md` | `architecture/MULTI_AGENT_SYSTEM_ARCHITECTURE.md` |

---

## 📝 Document Relationships

### Core Documents (Always Reference These)
1. **Claude.md** - Project rules and standards
2. **AGENT_INTERFACES.md** - How agents communicate
3. **INTERFACE_SPECIFICATION.md** - Data format standards
4. **DATA_LAYER_INTERFACES.md** - Column specifications

### Architecture Layer (System Design)
- Describes **WHAT** the system does and **WHY**
- References: Claude.md, AGENT_INTERFACES.md

### Interface Layer (Contracts)
- Describes **HOW** components interact
- References: Architecture docs, Claude.md

### Specification Layer (Implementation Details)
- Describes **EXACTLY HOW** to implement
- References: Interface docs, Architecture docs

### Module Layer (API References)
- Describes **SPECIFIC FUNCTIONS** and their usage
- References: Interface docs, Specification docs

### Feature Layer (Feature Documentation)
- Describes **COMPLETE FEATURES** end-to-end
- References: All above layers as needed

---

## 🔄 Documentation Update Triggers

| **Code Change** | **Update Required** |
|----------------|---------------------|
| New function added | Module docs → Interface docs (if signature changed) |
| New agent created | Architecture docs → Interface docs → Module docs |
| Data structure modified | INTERFACE_SPECIFICATION.md → DATA_LAYER_INTERFACES.md |
| New column added | DATA_LAYER_INTERFACES.md → related JSON files |
| Signal logic changed | specs/SIGNAL_GENERATION_SPEC.md → STRATEGY_LAYER_INTERFACE.md |
| New feature added | features/ → README.md index |
| API endpoint changed | specs/API_INTEGRATION_SPEC.md → HELPER_LAYER_INTERFACE.md |

---

## 🎯 Navigation Shortcuts

### For New Developers
1. Start: `README.md` (ROOT)
2. Then: `architecture/ARCHITECTURE_OVERVIEW.md`
3. Then: `AGENT_INTERFACES.md`
4. Then: Agent-specific architecture docs

### For Agent Development
1. Start: `architecture/[AGENT]_ARCHITECTURE.md`
2. Then: `interfaces/[LAYER]_INTERFACE.md`
3. Then: `modules/[LAYER]_MODULES.md`
4. Reference: `functions/[AGENT]_FUNCTIONS.md`

### For Feature Addition
1. Start: Related agent architecture doc
2. Then: Related interface doc
3. Then: Create new feature doc in `features/`
4. Update: This map and `README.md`

### For Debugging
1. Check: Module docs for API reference
2. Check: Interface docs for contract
3. Check: Specification docs for details
4. Check: Architecture docs for design intent

---

## 📊 Document Status Matrix

| Category | Count | Status | Needs Work |
|----------|-------|--------|------------|
| Architecture | 8 | ✅ Complete | - |
| Interfaces | 8 | ✅ Complete | - |
| Specifications | 8 | ✅ Complete | - |
| Features | 5 | ✅ Complete | - |
| Modules | 5 | ✅ Complete | - |
| Functions | 2 | ⚠️ Partial | Strategy/Service functions |
| User Guides | 4 | ✅ Complete | - |
| Management | 4 | ✅ Complete | - |

**Total Documents**: 54

---

## 🔗 External References

- **refer/debug_json/**: Column specification JSON files
- **config/**: Configuration file documentation
- **project/**: Source code with inline documentation

---

**Maintained by**: Orchestrator Agent
**Update Frequency**: On major structural changes
**Last Review**: 2025-10-13
