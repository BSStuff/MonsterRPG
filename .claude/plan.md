# Feature: Unity WebGL Proof of Concept

## Status
- **Phase**: plan
- **Status**: active
- **Progress**: 25/28 tasks complete
- **Last Updated**: 2026-03-06

---

## Feature Scope

### Description
Build a minimal Unity WebGL client that connects to the existing ElementsRPG FastAPI backend and demonstrates the core game loop: register/login, view owned monsters, fight enemies, see rewards. This is a proof-of-concept to validate the full-stack integration (Unity WebGL -> REST API -> Supabase Auth -> PostgreSQL) before investing in production art, animations, and polish.

### Acceptance Criteria
1. An empty Unity WebGL build deploys to Vercel and loads in a browser (day-one validation)
2. A player can register a new account or log in with existing credentials
3. After login, the player sees a list of their owned monsters with name, level, and element type
4. The player can start a combat encounter, advance rounds, and see HP changes
5. After combat ends, the player sees XP and gold rewards
6. Game state persists between sessions (save/load via backend)
7. Token refresh works transparently (401 -> refresh -> retry)
8. The entire flow works from a Vercel-hosted WebGL build hitting the Render-hosted backend

### Out of Scope (explicitly skipped)
- Animations, particle effects, sound, music
- Taming, crafting, idle systems, life skills, action queue
- Team management (combat fallback creates a starter team)
- Premium/subscription/ads
- Real monster art (use colored rectangles with element label)
- OAuth / magic links (email+password only)
- CI-based Unity builds (manual build for PoC)

---

## Tasks

### Phase 0 -- Day-One Validation (empty build -> Vercel)
**Goal**: Prove that an empty Unity WebGL project builds and deploys to Vercel before writing any game code. Catches IL2CPP, stripping, and hosting issues immediately.

- [x] `user` | **T0.1** Install Unity 6 LTS (6000.0) via Unity Hub with WebGL Build Support module | complete
- [x] `user` | **T0.2** Create Unity project at `ElementsRPG/` folder -- 2D Core template, Company Name "ElementsRPG", Product Name "ElementsRPG" | complete
- [x] `user` | **T0.3** Configure Player Settings for WebGL -- Managed Stripping Level "Minimal", Compression "Brotli", IL2CPP Code Gen "Faster (Smaller) Builds", Decompression Fallback OFF, Name Files As Hashes ON, Enable Exceptions "Explicitly Thrown Only" | complete
- [x] `implementation-agent` | **T0.4** Add `Assets/link.xml` to protect Newtonsoft.Json from IL2CPP stripping | complete
- [x] `implementation-agent` | **T0.5** Add `com.unity.nuget.newtonsoft-json` package via Packages/manifest.json | complete
- [x] `implementation-agent` | **T0.6** Add Unity-specific entries to root `.gitignore` | complete
- [x] `implementation-agent` | **T0.7** Update `vercel.json` -- add `"outputDirectory": "webgl-build"` field | complete
- [ ] `user` | **T0.8** Build WebGL to `webgl-build/`, commit, push, verify Vercel deploys and Unity splash loads | pending

**Parallelizable**: T0.2-T0.6 in one agent pass. T0.7 independent.

---

### Phase 1 -- Backend Preparation
**Goal**: Update CORS config so the WebGL client can reach the backend.

- [x] `implementation-agent` | **T1.1** Add `http://localhost:5500` to default CORS origins in `src/elements_rpg/api/config.py` | complete
- [ ] `user` | **T1.2** Add Vercel deployment URL to `ELEMENTS_CORS_ORIGINS` env var on Render dashboard | pending
- [x] `research-agent` | **T1.3** Verify API contract: confirm health, auth, save, combat, monster endpoints match plan's Scene->API Mapping | complete

**Parallelizable**: T1.1 and T1.3 in parallel. T1.2 is manual.

---

### Phase 2 -- C# Foundation (API Client + Models)
**Goal**: Build the HTTP client layer and C# data models. Test in Unity Editor against local backend.

- [x] `implementation-agent` | **T2.1** Create `GameConfig.cs` -- singleton, loads `StreamingAssets/config.json`, exposes `ApiBaseUrl` | complete
- [x] `implementation-agent` | **T2.2** Create `StreamingAssets/config.json` with `{ "apiBaseUrl": "http://localhost:8000" }` | complete
- [x] `implementation-agent` | **T2.3** Create `ApiModels.cs` -- all serializable C# data classes for API communication | complete
- [x] `implementation-agent` | **T2.4** Create `ApiClient.cs` -- UnityWebRequest + coroutines, auth header injection, 401 retry with token refresh | complete
- [x] `implementation-agent` | **T2.5** Create `AuthManager.cs` -- singleton, register/login/refresh/logout, PlayerPrefs JWT storage | complete
- [x] `implementation-agent` | **T2.6** Create `SaveApi.cs` -- LoadSave, CreateNewSave, SaveGame wrappers | complete
- [x] `implementation-agent` | **T2.7** Create `CombatApi.cs` -- StartCombat, ExecuteRound, FinishCombat wrappers | complete
- [x] `implementation-agent` | **T2.8** Create `MonsterApi.cs` -- GetBestiary, GetOwnedMonsters wrappers | complete
- [x] `implementation-agent` | **T2.9** Create `EconomyApi.cs` -- GetBalance wrapper | complete

**Dependencies**: T2.4 depends on T2.1+T2.3. T2.5 depends on T2.4. T2.6-T2.9 depend on T2.4+T2.5 but are independent of each other.

---

### Phase 3 -- Scenes and UI
**Goal**: Build the 4 scenes with functional UI connected to the API layer.

- [x] `implementation-agent` | **T3.1** Create `SceneData.cs` -- static class for cross-scene state (RawSaveJson, CurrentSave, SaveVersion, LastCombatResult) | complete
- [x] `implementation-agent` | **T3.2** Create Login scene + `LoginController.cs` -- email/password fields, sign in/up buttons, error display, auto-skip if already logged in | complete
- [x] `implementation-agent` | **T3.3** Create `MonsterListItem.prefab` + `MonsterListItem.cs` -- colored element square, name, level, type label | complete
- [x] `implementation-agent` | **T3.4** Create Home scene + `HomeController.cs` -- load save, monster scroll list, player info header, start combat button, logout | complete
- [x] `implementation-agent` | **T3.5** Create Combat scene + `CombatController.cs` -- HP bars, combat log, next round button, auto-finish flow | complete
- [x] `implementation-agent` | **T3.6** Create Results scene + `ResultsController.cs` -- victory/defeat, rewards display, continue button triggers save | complete
- [x] `implementation-agent` | **T3.7** Add all 4 scenes to Build Settings (Login=0, Home=1, Combat=2, Results=3) | complete

**Dependencies**: T3.1 first. T3.2+T3.3 parallel. T3.4 depends on T3.3. T3.5+T3.6 depend on T3.1. T3.7 last.

---

### Phase 4 -- WebGL Build and Deploy
**Goal**: Produce a working WebGL build, deploy to Vercel, verify full flow in browser.

- [ ] `user` | **T4.1** Update `config.json` with production API URL (Render backend URL) | pending
- [ ] `user` | **T4.2** Build WebGL to `webgl-build/` folder | pending
- [ ] `user` | **T4.3** Test locally with `npx serve webgl-build` | pending
- [ ] `user` | **T4.4** Commit and push -- enable Git LFS if needed for large .wasm/.data files | pending
- [ ] `user` | **T4.5** Smoke test on Vercel: register, view monsters, combat, results, persistence | pending

---

## Scene -> API Mapping

### Login Scene
| Action | Method | Endpoint | Auth | Body | Key Response |
|--------|--------|----------|------|------|-------------|
| Sign Up | POST | `/auth/register` | No | `{ email, password, username }` | `access_token, refresh_token, user.id` |
| Sign In | POST | `/auth/login` | No | `{ email, password }` | `access_token, refresh_token, user.id` |

### Home Scene
| Action | Method | Endpoint | Auth | Body | Key Response |
|--------|--------|----------|------|------|-------------|
| Load save | GET | `/saves/` | Yes | -- | Full `GameSaveData` JSON |
| New save | POST | `/saves/new` | Yes | -- | Fresh default `GameSaveData` |

### Combat Scene
| Action | Method | Endpoint | Auth | Body | Key Response |
|--------|--------|----------|------|------|-------------|
| Start | POST | `/combat/start` | Yes | `{ enemy_species_ids, enemy_level }` | `session_id, state` |
| Round | POST | `/combat/{id}/round` | Yes | -- | `state, actions[]` |
| Finish | POST | `/combat/{id}/finish` | Yes | -- | `winner, rewards` |

### Results Scene
| Action | Method | Endpoint | Auth | Body | Key Response |
|--------|--------|----------|------|------|-------------|
| Save | POST | `/saves/` | Yes | `{ save_data, expected_version }` | `success, version` |

### Background (401 handling)
| Action | Method | Endpoint | Auth | Body | Key Response |
|--------|--------|----------|------|------|-------------|
| Refresh | POST | `/auth/refresh` | No | `{ refresh_token }` | `access_token, refresh_token` |

**Total: 9 endpoints** (out of 65+)

---

## C# Script Inventory

### Config (`Assets/Scripts/Config/`)
| Script | Purpose |
|--------|---------|
| `GameConfig.cs` | Singleton. Loads StreamingAssets/config.json. Provides ApiBaseUrl. |

### Models (`Assets/Scripts/Models/`)
| Script | Purpose |
|--------|---------|
| `ApiModels.cs` | All serializable C# classes: ApiResponse<T>, AuthRequest/Response, MonsterSpecies, MonsterInstance, PlayerData, GameSaveData, CombatStartRequest/Response, CombatState, CombatMonster, CombatAction, CombatRoundResponse, CombatFinishResponse, CombatRewards, BalanceResponse, SaveRequest/Response |

### API (`Assets/Scripts/API/`)
| Script | Purpose |
|--------|---------|
| `ApiClient.cs` | UnityWebRequest + coroutines, auth header, 401 retry |
| `AuthManager.cs` | Singleton. Register/login/refresh/logout. PlayerPrefs JWT storage. |
| `SaveApi.cs` | LoadSave, CreateNewSave, SaveGame |
| `CombatApi.cs` | StartCombat, ExecuteRound, FinishCombat |
| `MonsterApi.cs` | GetBestiary, GetOwnedMonsters |
| `EconomyApi.cs` | GetBalance |

### UI (`Assets/Scripts/UI/`)
| Script | Purpose |
|--------|---------|
| `SceneData.cs` | Static cross-scene state bus |
| `LoginController.cs` | Login scene controller |
| `HomeController.cs` | Home scene controller |
| `MonsterListItem.cs` | Monster row prefab controller |
| `CombatController.cs` | Combat scene controller |
| `ResultsController.cs` | Results scene controller |

---

## Element Color Map

| Element | Hex | RGB (Unity) |
|---------|-----|-------------|
| water | #3B82F6 | (0.23, 0.51, 0.96) |
| fire | #EF4444 | (0.94, 0.27, 0.27) |
| grass | #22C55E | (0.13, 0.77, 0.37) |
| electric | #EAB308 | (0.92, 0.70, 0.03) |
| wind | #A3E635 | (0.64, 0.90, 0.21) |
| ground | #92400E | (0.57, 0.25, 0.05) |
| rock | #78716C | (0.47, 0.44, 0.42) |
| dark | #6B21A8 | (0.42, 0.13, 0.66) |
| light | #FDE047 | (0.99, 0.88, 0.28) |
| ice | #67E8F9 | (0.40, 0.91, 0.98) |

---

## GameSaveData Passthrough Strategy

The full GameSaveData JSON contains many fields the PoC doesn't display. Strategy:
1. **On load**: Parse full response into Newtonsoft `JObject`. Extract `player` and `monsters` into typed C# objects. Store entire blob as `SceneData.RawSaveJson`.
2. **On save**: Send stored raw JSON back as `save_data`. No data loss on untouched fields.
3. **Why it works**: Combat rewards are applied server-side by `/combat/finish`. Save data is already current.

---

## Blockers / User Decisions Required

| Item | Type | Impact | Needed Before |
|------|------|--------|---------------|
| Unity 6 LTS installed with WebGL module? | User confirmation | Cannot build without it | T0.1 |
| Render backend URL | User must provide | Required for config.json and CORS | T1.2, T4.1 |
| Vercel deployment URL | User must provide | Required for CORS on Render | T1.2 |
| Supabase project running? | User confirmation | Backend needs it for auth | T1.2 |
| Git LFS for WebGL build artifacts? | User decision | .wasm/.data may be 10-30MB | T4.4 |
| Folder rename ElementsRPG -> unity | Permission denied (2026-03-06) | Cosmetic only; proceeding with `ElementsRPG/` | N/A |

---

## link.xml Contents

```xml
<linker>
  <assembly fullname="Newtonsoft.Json" preserve="all"/>
  <assembly fullname="System.Runtime.Serialization" preserve="all"/>
</linker>
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Newtonsoft.Json stripped by IL2CPP | Medium | All API calls fail | link.xml + Minimal stripping + Phase 0 validation |
| CORS blocks Vercel->Render | High if forgotten | All API calls fail | Explicit CORS tasks in Phase 1 |
| Combat session lost on backend restart | Low | 404 mid-combat | CombatController shows error, returns to Home |
| Token expires during play | Low | 401 on next call | ApiClient auto-refreshes and retries |
| GameSaveData schema mismatch | Medium | Save/load fails | Passthrough strategy for unused fields |

---

## Progress Log

| Timestamp | Agent | Task | Status | Notes |
|-----------|-------|------|--------|-------|
| 2026-03-05 | research-agent | API surface research | complete | 65+ endpoints cataloged, 9 needed for PoC |
| 2026-03-05 | research-agent | Unity WebGL research | complete | Coroutines, Newtonsoft, UGUI, Unity 6 LTS |
| 2026-03-05 | planning-agent | Plan created | complete | 28 tasks across 5 phases |
| 2026-03-06 | implementation-agent | T0.6 Update .gitignore | complete | Added Unity-specific ignore entries under # Unity header |
| 2026-03-06 | implementation-agent | T0.7 Update vercel.json | complete | Added outputDirectory: webgl-build top-level field |
| 2026-03-06 | implementation-agent | T1.1 Update CORS config | complete | Added http://localhost:5500 to default cors_origins |
| 2026-03-06 | implementation-agent | T0.4 Add link.xml | complete | Created ElementsRPG/Assets/link.xml preserving Newtonsoft.Json and System.Runtime.Serialization |
| 2026-03-06 | implementation-agent | T0.5 Add Newtonsoft.Json package | complete | Added com.unity.nuget.newtonsoft-json 3.2.1 to manifest.json |
| 2026-03-06 | implementation-agent | Fix .gitignore paths | complete | Replaced unity/ prefixes with ElementsRPG/ to match actual project folder |
| 2026-03-06 | implementation-agent | T2.1 Create GameConfig.cs | complete | Singleton MonoBehaviour with DontDestroyOnLoad, loads config.json via UnityWebRequest, falls back to localhost:8000 |
| 2026-03-06 | implementation-agent | T2.2 Create config.json | complete | StreamingAssets/config.json with apiBaseUrl default |
| 2026-03-06 | implementation-agent | T2.3 Create ApiModels.cs | complete | 23 serializable C# classes with JsonProperty attributes, GameSaveData uses JsonExtensionData for round-trip preservation |
| 2026-03-06 | implementation-agent | T2.4 Create ApiClient.cs | complete | Singleton MonoBehaviour, Get/Post/PostNoBody generic methods, auth header injection, 401 auto-refresh + retry, ApiResponse envelope unwrapping, error parsing |
| 2026-03-06 | implementation-agent | T2.5 Create AuthManager.cs | complete | Singleton MonoBehaviour, Login/Register/RefreshToken/Logout, PlayerPrefs JWT persistence, PostAuth shared helper |
| 2026-03-06 | implementation-agent | T2.6 Create SaveApi.cs | complete | Static class, LoadSave (JObject passthrough), CreateNewSave, SaveGame with optimistic locking |
| 2026-03-06 | implementation-agent | T2.7 Create CombatApi.cs | complete | Static class, StartCombat/ExecuteRound/FinishCombat wrapping ApiClient |
| 2026-03-06 | implementation-agent | T2.8 Create MonsterApi.cs | complete | Static class, GetBestiary (public) and GetOwnedMonsters (auth) |
| 2026-03-06 | implementation-agent | T2.9 Create EconomyApi.cs | complete | Static class, GetBalance wrapper |
| 2026-03-06 | research-agent | T1.3 Verify API contract | complete | 9/9 endpoints exist and match plan. 8/9 use standard SuccessResponse envelope. 1 discrepancy: POST /saves/ returns SaveConfirmation directly (no `data` wrapper) -- Unity SaveApi must handle flat response shape. |
| 2026-03-06 | implementation-agent | T3.1 Create SceneData.cs | complete | Static class with RawSaveData (JObject), CurrentPlayer, CurrentMonsters, SaveVersion, LastCombatResult, Clear() |
| 2026-03-06 | implementation-agent | T3.2 Create LoginController.cs | complete | Login/register toggle, input validation, auto-skip if logged in, waits for GameConfig.IsReady, error auto-hide |
| 2026-03-06 | implementation-agent | T3.3 Create MonsterListItem.cs | complete | Element color map (10 elements), Setup() populates name/level/type with colored icon and text |
| 2026-03-06 | implementation-agent | T3.4 Create HomeController.cs | complete | Loads save (auto-creates on 404), populates monster scroll list, fetches balance, combat/logout buttons |
| 2026-03-06 | implementation-agent | T3.5 Create CombatController.cs | complete | Full combat flow: start session, advance rounds, HP bars, combat log with scroll, finish + transition to Results |
| 2026-03-06 | implementation-agent | T3.6 Create ResultsController.cs | complete | Victory/defeat display, rewards, save on continue with optimistic locking, graceful save failure handling |
| 2026-03-06 | implementation-agent | T3.7 ProjectSetup.cs editor script | complete | Auto-creates all 4 scenes (Login, Home, Combat, Results), MonsterListItem prefab, singletons (GameConfig, ApiClient, AuthManager), wires all serialized fields via SerializedObject, configures Build Settings |
| 2026-03-06 | user | T0.1 Install Unity 6 LTS | complete | Unity 6 LTS installed with WebGL Build Support module |
| 2026-03-06 | user | T0.2 Create Unity project | complete | Created Unity project at ElementsRPG/ folder |
| 2026-03-06 | user | T0.3 Configure Player Settings | complete | WebGL Player Settings configured during project creation |
