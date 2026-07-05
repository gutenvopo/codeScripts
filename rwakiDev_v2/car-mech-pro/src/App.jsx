import { useState, useEffect, useRef, useCallback } from "react";
import { initializeApp } from "firebase/app";
import { getFirestore, collection, getDocs, addDoc, deleteDoc, updateDoc, doc, Timestamp } from "firebase/firestore";
import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth";
import { firebaseConfig } from "./firebaseConfig";

const app  = initializeApp(firebaseConfig);
const db   = getFirestore(app);
const auth = getAuth(app);

// ═══════════════════════════════════════════════════════════════
// ICONS
// ═══════════════════════════════════════════════════════════════
const WrenchIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:20,height:20}}><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
const CarIcon    = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{width:20,height:20}}><path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2h-2"/><circle cx="9" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>;
const PlusIcon   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{width:16,height:16}}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const TrashIcon  = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{width:15,height:15}}><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>;
const EditIcon   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{width:15,height:15}}><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
const SaveIcon   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{width:15,height:15}}><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>;
const CancelIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{width:15,height:15}}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
const LogoutIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{width:18,height:18}}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>;
const FilterIcon = () => <svg viewBox="0 0 24 24" fill="currentColor" style={{width:10,height:10,marginLeft:3,flexShrink:0}}><path d="M4 6h16v2l-6 7v5l-4-2v-3L4 8V6z"/></svg>;
const AscIcon    = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{width:13,height:13}}><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>;
const DescIcon   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{width:13,height:13}}><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>;

// ═══════════════════════════════════════════════════════════════
// COLUMN DEFINITIONS
// type: "text" | "number" | "date"  — drives sort logic
// ═══════════════════════════════════════════════════════════════
const COLUMNS = [
  { label:"Document ID",   field:null,              filterable:false, type:"text"   },
  { label:"Email Address", field:"username",         filterable:true,  type:"text"   },
  { label:"First Name",    field:"cust_first_name",  filterable:true,  type:"text"   },
  { label:"Last Name",     field:"cust_last_name",   filterable:true,  type:"text"   },
  { label:"Cellphone",     field:"cellphone",        filterable:true,  type:"text"   },
  { label:"Vehicle Make",  field:"vehicle_make",     filterable:true,  type:"text"   },
  { label:"Vehicle Model", field:"vehicle_model",    filterable:true,  type:"text"   },
  { label:"Year",          field:"vehicle_year",     filterable:true,  type:"number" },
  { label:"Date Joined",   field:"Date_cust_joined", filterable:true,  type:"date"   },
  { label:"Actions",       field:null,              filterable:false, type:"text"   },
];

const emptyForm      = { username:"", cust_first_name:"", cust_last_name:"", cellphone:"", vehicle_make:"", vehicle_model:"", vehicle_year:"" };
const makeBlankFilter = () => ({ search:"", excluded: new Set() });
const makeAllFilters  = () => Object.fromEntries(COLUMNS.filter(c => c.filterable).map(c => [c.field, makeBlankFilter()]));

// Shared small button styles
const S = {
  microBtn:        { background:"rgba(249,115,22,0.1)", border:"1px solid rgba(249,115,22,0.25)", color:"#f97316", borderRadius:4, padding:"2px 7px", fontSize:10, cursor:"pointer" },
  footerBtnGhost:  { background:"transparent", border:"1px solid #334155", color:"#94a3b8", borderRadius:7, padding:"6px 12px", fontSize:12, cursor:"pointer" },
  footerBtnOrange: { background:"linear-gradient(135deg,#f97316,#ea580c)", border:"none", color:"#fff", borderRadius:7, padding:"6px 14px", fontSize:12, fontWeight:600, cursor:"pointer" },
  sortBtnBase:     { display:"flex", alignItems:"center", gap:5, flex:1, justifyContent:"center", border:"1px solid #1e293b", borderRadius:7, padding:"7px 6px", fontSize:11, fontWeight:600, cursor:"pointer", transition:"all .15s" },
};

// ═══════════════════════════════════════════════════════════════
// SORT LABEL HELPER  — returns the right A→Z / Z→A / 0→9 labels
// ═══════════════════════════════════════════════════════════════
function sortLabels(type) {
  if (type === "number") return { asc:"0 → 9",  desc:"9 → 0"  };
  if (type === "date")   return { asc:"Oldest First", desc:"Newest First" };
  return                        { asc:"A → Z",  desc:"Z → A"  };
}

// ═══════════════════════════════════════════════════════════════
// COLUMN FILTER + SORT DROPDOWN  (single combined panel per column)
// ═══════════════════════════════════════════════════════════════
function ColumnDropdown({ col, allCustomers, colFilter, sortState, onChange, onClear, onSort, fmtDate }) {
  const [open,        setOpen]        = useState(false);
  const [localSearch, setLocalSearch] = useState("");
  const [excluded,    setExcluded]    = useState(new Set(colFilter.excluded));
  const panelRef = useRef(null);
  const btnRef   = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const h = e => {
      if (panelRef.current && !panelRef.current.contains(e.target) &&
          btnRef.current   && !btnRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);

  useEffect(() => { setExcluded(new Set(colFilter.excluded)); }, [colFilter.excluded]);

  // Unique values for the checklist
  const allValues = Array.from(
    new Set(allCustomers.map(c =>
      col.field === "Date_cust_joined" ? fmtDate(c[col.field]) : String(c[col.field] ?? "—")
    ))
  ).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

  const visibleValues = localSearch.trim()
    ? allValues.filter(v => v.toLowerCase().includes(localSearch.toLowerCase()))
    : allValues;

  const isFilterActive = colFilter.search !== "" || colFilter.excluded.size > 0;
  const isSortActive   = sortState.field === col.field;
  const isActive       = isFilterActive || isSortActive;

  const toggleExclude = val => setExcluded(prev => {
    const next = new Set(prev); next.has(val) ? next.delete(val) : next.add(val); return next;
  });

  const applyAndClose = () => { onChange({ search: colFilter.search, excluded }); setOpen(false); };
  const handleText    = val => onChange({ search: val, excluded: colFilter.excluded });

  const handleSort = dir => {
    onSort(col.field === sortState.field && sortState.dir === dir ? null : { field: col.field, dir, type: col.type });
    setOpen(false);
  };

  const labels = sortLabels(col.type);

  return (
    <div style={{ position:"relative", display:"inline-block", width:"100%" }}>

      {/* ── Header trigger button ── */}
      <button
        ref={btnRef}
        onClick={() => setOpen(o => !o)}
        style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          width:"100%", background:"transparent", border:"none", cursor:"pointer",
          color: isActive ? "#f97316" : "#64748b",
          fontWeight:600, fontSize:11, letterSpacing:"0.05em", textTransform:"uppercase",
          padding:0, gap:4,
        }}
      >
        <span style={{display:"flex", alignItems:"center", gap:3}}>
          {col.label}
          {/* Show current sort arrow next to label */}
          {isSortActive && (
            <span style={{color:"#f97316", marginLeft:2}}>
              {sortState.dir === "asc" ? "↑" : "↓"}
            </span>
          )}
          <FilterIcon/>
        </span>
        {isActive && (
          <span style={{
            background:"#f97316", color:"#fff", borderRadius:"50%",
            width:14, height:14, fontSize:9, display:"flex",
            alignItems:"center", justifyContent:"center", fontWeight:700, flexShrink:0,
          }}>●</span>
        )}
      </button>

      {/* ── Dropdown panel ── */}
      {open && (
        <div ref={panelRef} style={{
          position:"absolute", top:"calc(100% + 8px)", left:0, zIndex:500,
          background:"#0f172a", border:"1px solid #334155", borderRadius:10,
          boxShadow:"0 16px 40px rgba(0,0,0,0.65)", width:240, overflow:"hidden",
        }}>

          {/* ── SECTION 1: Sort ── */}
          <div style={{padding:"11px 12px 10px", borderBottom:"1px solid #1e293b"}}>
            <p style={{color:"#64748b", fontSize:10, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.05em", margin:"0 0 8px"}}>
              Sort
            </p>
            <div style={{display:"flex", gap:6}}>
              {/* Ascending */}
              <button
                onClick={() => handleSort("asc")}
                style={{
                  ...S.sortBtnBase,
                  background: isSortActive && sortState.dir === "asc" ? "rgba(249,115,22,0.15)" : "#1e293b",
                  borderColor: isSortActive && sortState.dir === "asc" ? "#f97316" : "#1e293b",
                  color: isSortActive && sortState.dir === "asc" ? "#f97316" : "#94a3b8",
                }}
              >
                <AscIcon/> {labels.asc}
              </button>
              {/* Descending */}
              <button
                onClick={() => handleSort("desc")}
                style={{
                  ...S.sortBtnBase,
                  background: isSortActive && sortState.dir === "desc" ? "rgba(249,115,22,0.15)" : "#1e293b",
                  borderColor: isSortActive && sortState.dir === "desc" ? "#f97316" : "#1e293b",
                  color: isSortActive && sortState.dir === "desc" ? "#f97316" : "#94a3b8",
                }}
              >
                <DescIcon/> {labels.desc}
              </button>
            </div>
            {isSortActive && (
              <button
                onClick={() => { onSort(null); setOpen(false); }}
                style={{marginTop:6, background:"none", border:"none", color:"#64748b", fontSize:11, cursor:"pointer", padding:0}}
              >✕ Clear sort</button>
            )}
          </div>

          {/* ── SECTION 2: Text / partial match filter ── */}
          <div style={{padding:"10px 12px 8px", borderBottom:"1px solid #1e293b"}}>
            <p style={{color:"#64748b", fontSize:10, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.05em", margin:"0 0 6px"}}>
              Text Filter
            </p>
            <input
              autoFocus
              style={{width:"100%", background:"#1e293b", border:"1px solid #334155", borderRadius:7, color:"#e2e8f0", padding:"7px 10px", fontSize:12, outline:"none", boxSizing:"border-box"}}
              placeholder="Type any characters to match…"
              value={colFilter.search}
              onChange={e => handleText(e.target.value)}
            />
            {colFilter.search && (
              <button onClick={() => handleText("")} style={{marginTop:5, background:"none", border:"none", color:"#64748b", fontSize:11, cursor:"pointer", padding:0}}>
                ✕ Clear text
              </button>
            )}
          </div>

          {/* ── SECTION 3: Include / exclude checklist ── */}
          <div style={{padding:"10px 12px 6px"}}>
            <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:7}}>
              <p style={{color:"#64748b", fontSize:10, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.05em", margin:0}}>
                Include / Exclude
              </p>
              <div style={{display:"flex", gap:6}}>
                <button onClick={() => setExcluded(new Set())}              style={S.microBtn}>All</button>
                <button onClick={() => setExcluded(new Set(visibleValues))} style={S.microBtn}>None</button>
              </div>
            </div>
            <input
              style={{width:"100%", background:"#1e293b", border:"1px solid #1e293b", borderRadius:6, color:"#94a3b8", padding:"5px 8px", fontSize:11, outline:"none", marginBottom:7, boxSizing:"border-box"}}
              placeholder="Search values in list…"
              value={localSearch}
              onChange={e => setLocalSearch(e.target.value)}
            />
            <div style={{maxHeight:150, overflowY:"auto", display:"flex", flexDirection:"column", gap:1}}>
              {visibleValues.length === 0 && (
                <p style={{color:"#475569", fontSize:11, textAlign:"center", padding:"8px 0", margin:0}}>No values found</p>
              )}
              {visibleValues.map(val => (
                <label key={val} style={{display:"flex", alignItems:"center", gap:8, cursor:"pointer", padding:"4px 6px", borderRadius:5, userSelect:"none", background: excluded.has(val) ? "rgba(239,68,68,0.07)" : "transparent"}}>
                  <input type="checkbox" checked={!excluded.has(val)} onChange={() => toggleExclude(val)}
                    style={{accentColor:"#f97316", width:13, height:13, cursor:"pointer", flexShrink:0}}/>
                  <span style={{fontSize:12, color: excluded.has(val) ? "#475569" : "#cbd5e1", textDecoration: excluded.has(val) ? "line-through" : "none", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis"}}>
                    {val}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* ── Footer ── */}
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", padding:"8px 12px 11px", borderTop:"1px solid #1e293b", gap:6}}>
            <button
              onClick={() => { onClear(); setExcluded(new Set()); setLocalSearch(""); setOpen(false); }}
              style={S.footerBtnGhost}
            >Clear Filters</button>
            <button onClick={applyAndClose} style={S.footerBtnOrange}>Apply ✓</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════════
export default function App() {
  const [user,       setUser]       = useState(null);
  const [authReady,  setAuthReady]  = useState(false);
  const [loginForm,  setLoginForm]  = useState({ email:"", password:"" });
  const [loginErr,   setLoginErr]   = useState("");
  const [customers,  setCustomers]  = useState([]);
  const [loading,    setLoading]    = useState(false);
  const [toast,      setToast]      = useState(null);
  const [showAdd,    setShowAdd]    = useState(false);
  const [addForm,    setAddForm]    = useState(emptyForm);
  const [addErr,     setAddErr]     = useState("");
  const [editId,     setEditId]     = useState(null);
  const [editForm,   setEditForm]   = useState({});
  const [deleteId,   setDeleteId]   = useState(null);
  const [colFilters, setColFilters] = useState(makeAllFilters);
  // sortState: null | { field, dir: "asc"|"desc", type: "text"|"number"|"date" }
  const [sortState,  setSortState]  = useState(null);

  // ── Auth ─────────────────────────────────────────────────────
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, u => { setUser(u); setAuthReady(true); });
    return unsub;
  }, []);
  useEffect(() => { if (user) fetchCustomers(); }, [user]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const snap = await getDocs(collection(db, "customers"));
      setCustomers(snap.docs.map(d => ({ id: d.id, ...d.data() })));
    } catch(e) { showToast("Error fetching data: " + e.message, "error"); }
    setLoading(false);
  };

  const showToast = (msg, type="success") => { setToast({ msg, type }); setTimeout(() => setToast(null), 3500); };

  // ── Login ────────────────────────────────────────────────────
  const handleLogin = async e => {
    e.preventDefault(); setLoginErr("");
    try { await signInWithEmailAndPassword(auth, loginForm.email, loginForm.password); }
    catch { setLoginErr("Invalid email or password. Please try again."); }
  };

  // ── Add ──────────────────────────────────────────────────────
  const handleAdd = async e => {
    e.preventDefault(); setAddErr("");
    const required = ["username","cust_first_name","cust_last_name","vehicle_make","vehicle_model","vehicle_year"];
    for (const f of required) if (!addForm[f].trim()) { setAddErr(`Please fill in: ${f.replace(/_/g," ")}`); return; }
    try {
      const payload = {
        username: addForm.username.trim(), cust_first_name: addForm.cust_first_name.trim(),
        cust_last_name: addForm.cust_last_name.trim(), cellphone: addForm.cellphone?.trim() || "",
        vehicle_make: addForm.vehicle_make.trim(), vehicle_model: addForm.vehicle_model.trim(),
        vehicle_year: parseInt(addForm.vehicle_year), Date_cust_joined: Timestamp.now(),
      };
      const ref = await addDoc(collection(db, "customers"), payload);
      setCustomers(prev => [...prev, { id: ref.id, ...payload }]);
      setAddForm(emptyForm); setShowAdd(false); showToast("Customer added successfully!");
    } catch(e) { setAddErr("Error adding customer: " + e.message); }
  };

  // ── Delete ───────────────────────────────────────────────────
  const handleDelete = async () => {
    try {
      await deleteDoc(doc(db, "customers", deleteId));
      setCustomers(prev => prev.filter(c => c.id !== deleteId));
      setDeleteId(null); showToast("Customer deleted.");
    } catch(e) { showToast("Error deleting: " + e.message, "error"); }
  };

  // ── Edit ─────────────────────────────────────────────────────
  const startEdit  = c  => { setEditId(c.id); setEditForm({ ...c }); };
  const cancelEdit = () => { setEditId(null); setEditForm({}); };

  const handleSaveEdit = async id => {
    try {
      const payload = {
        username: editForm.username, cust_first_name: editForm.cust_first_name,
        cust_last_name: editForm.cust_last_name, cellphone: editForm.cellphone || "",
        vehicle_make: editForm.vehicle_make, vehicle_model: editForm.vehicle_model,
        vehicle_year: parseInt(editForm.vehicle_year),
      };
      await updateDoc(doc(db, "customers", id), payload);
      setCustomers(prev => prev.map(c => c.id === id ? { ...c, ...payload } : c));
      setEditId(null); showToast("Record updated successfully!");
    } catch(e) { showToast("Error updating: " + e.message, "error"); }
  };

  // ── Date formatter ───────────────────────────────────────────
  const fmtDate = ts => {
    if (!ts) return "—";
    if (ts.toDate)              return ts.toDate().toLocaleDateString("en-KE", { year:"numeric", month:"short", day:"numeric" });
    if (typeof ts === "string") { const d = new Date(ts); return isNaN(d) ? ts : d.toLocaleDateString("en-KE", { year:"numeric", month:"short", day:"numeric" }); }
    if (ts instanceof Date)     return ts.toLocaleDateString("en-KE", { year:"numeric", month:"short", day:"numeric" });
    if (ts.seconds)             return new Date(ts.seconds * 1000).toLocaleDateString("en-KE", { year:"numeric", month:"short", day:"numeric" });
    return "—";
  };

  // Helper: get raw timestamp as ms for sorting dates
  const toMs = ts => {
    if (!ts) return 0;
    if (ts.toDate)    return ts.toDate().getTime();
    if (ts.seconds)   return ts.seconds * 1000;
    if (ts instanceof Date) return ts.getTime();
    if (typeof ts === "string") { const d = new Date(ts); return isNaN(d) ? 0 : d.getTime(); }
    return 0;
  };

  // ── Filter helpers ───────────────────────────────────────────
  const updateFilter    = useCallback((field, patch) =>
    setColFilters(prev => ({ ...prev, [field]: { ...prev[field], ...patch } })), []);
  const clearFilter     = useCallback(field =>
    setColFilters(prev => ({ ...prev, [field]: makeBlankFilter() })), []);
  const clearAllFilters = () => { setColFilters(makeAllFilters()); setSortState(null); };

  const hasActiveFilters = Object.values(colFilters).some(f => f.search !== "" || f.excluded.size > 0);
  const hasAnyActive     = hasActiveFilters || sortState !== null;

  // ── Filter ───────────────────────────────────────────────────
  const filtered = customers.filter(c =>
    COLUMNS.filter(col => col.filterable).every(col => {
      const f = colFilters[col.field];
      if (!f) return true;
      const rawVal = col.field === "Date_cust_joined" ? fmtDate(c[col.field]) : String(c[col.field] ?? "—");
      if (f.search.trim() && !rawVal.toLowerCase().includes(f.search.toLowerCase())) return false;
      if (f.excluded.size > 0 && f.excluded.has(rawVal)) return false;
      return true;
    })
  );

  // ── Sort ─────────────────────────────────────────────────────
  const displayed = sortState ? [...filtered].sort((a, b) => {
    const { field, dir, type } = sortState;
    const mul = dir === "asc" ? 1 : -1;
    if (type === "date")   return mul * (toMs(a[field]) - toMs(b[field]));
    if (type === "number") return mul * ((Number(a[field]) || 0) - (Number(b[field]) || 0));
    return mul * String(a[field] ?? "").localeCompare(String(b[field] ?? ""), undefined, { sensitivity:"base" });
  }) : filtered;

  // ── Splash ───────────────────────────────────────────────────
  if (!authReady) return (
    <div style={styles.splash}><div style={styles.splashInner}>
      <div style={styles.splashLogo}><WrenchIcon/></div>
      <p style={styles.splashText}>Loading Car Mech Pro…</p>
    </div></div>
  );

  // ── Login ────────────────────────────────────────────────────
  if (!user) return (
    <div style={styles.loginPage}>
      <div style={styles.loginCard}>
        <div style={styles.loginLogo}>
          <div style={styles.logoCircle}><WrenchIcon/></div>
          <h1 style={styles.loginBrand}>Car Mech Pro</h1>
          <p style={styles.loginSub}>Customer Database Portal</p>
        </div>
        <form onSubmit={handleLogin} style={styles.loginForm}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Admin Email</label>
            <input style={styles.input} type="email" placeholder="admin@carmechpro.com"
              value={loginForm.email} onChange={e => setLoginForm(p => ({...p, email:e.target.value}))} required/>
          </div>
          <div style={styles.formGroup}>
            <label style={styles.label}>Password</label>
            <input style={styles.input} type="password" placeholder="••••••••"
              value={loginForm.password} onChange={e => setLoginForm(p => ({...p, password:e.target.value}))} required/>
          </div>
          {loginErr && <p style={styles.errMsg}>{loginErr}</p>}
          <button type="submit" style={styles.btnPrimary}>Sign In →</button>
        </form>
      </div>
    </div>
  );

  // ── Dashboard ────────────────────────────────────────────────
  return (
    <div style={styles.app}>

      {toast && <div style={{...styles.toast, background: toast.type==="error" ? "#ef4444" : "#22c55e"}}>{toast.msg}</div>}

      {/* Navbar */}
      <nav style={styles.nav}>
        <div style={styles.navBrand}>
          <div style={styles.navLogoCircle}><WrenchIcon/></div>
          <span style={styles.navTitle}>Car Mech Pro</span>
          <span style={styles.navBadge}>Admin</span>
        </div>
        <div style={styles.navRight}>
          <span style={styles.navUser}>{user.email}</span>
          <button onClick={() => signOut(auth)} style={styles.btnLogout}><LogoutIcon/> Sign Out</button>
        </div>
      </nav>

      {/* Page header */}
      <div style={styles.pageHeader}>
        <div>
          <h2 style={styles.pageTitle}>Customer Records</h2>
          <p style={styles.pageSub}>
            {displayed.length} of {customers.length} customers
            {sortState && <span style={{color:"#f97316", fontSize:12}}>· sorted by {COLUMNS.find(c=>c.field===sortState.field)?.label} {sortState.dir==="asc"?"↑":"↓"}</span>}
            {hasAnyActive && <button onClick={clearAllFilters} style={styles.clearBtn}>✕ Clear all</button>}
          </p>
        </div>
        <div style={styles.headerActions}>
          <button style={styles.btnPrimary} onClick={() => { setShowAdd(true); setAddErr(""); }}>
            <PlusIcon/> Add Customer
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={styles.content}>
        {loading ? (
          <div style={styles.loadingBox}>
            <div style={styles.spinner}/>
            <p style={{color:"#94a3b8", marginTop:12}}>Fetching records from Firebase…</p>
          </div>
        ) : (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  {COLUMNS.map(col => (
                    <th key={col.label} style={styles.th}>
                      {col.filterable ? (
                        <ColumnDropdown
                          col={col}
                          allCustomers={customers}
                          colFilter={colFilters[col.field]}
                          sortState={sortState ?? { field:null }}
                          fmtDate={fmtDate}
                          onChange={patch => updateFilter(col.field, patch)}
                          onClear={() => clearFilter(col.field)}
                          onSort={s => setSortState(s)}
                        />
                      ) : (
                        <span style={{color:"#64748b", fontWeight:600, fontSize:11, letterSpacing:"0.05em", textTransform:"uppercase"}}>{col.label}</span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayed.length === 0 ? (
                  <tr><td colSpan={COLUMNS.length} style={styles.emptyCell}>
                    No customers match the current filters.
                    {hasAnyActive && <button onClick={clearAllFilters} style={{...S.footerBtnOrange, marginLeft:14}}>Clear all</button>}
                  </td></tr>
                ) : displayed.map(c => (
                  <tr key={c.id}
                    style={editId===c.id ? styles.trEdit : styles.tr}
                    onMouseEnter={e => { if(editId!==c.id) e.currentTarget.style.background="#1e293b"; }}
                    onMouseLeave={e => { if(editId!==c.id) e.currentTarget.style.background="transparent"; }}>

                    {editId === c.id ? (
                      <>
                        <td style={styles.tdId} title={c.id}>{c.id}</td>
                        {["username","cust_first_name","cust_last_name","cellphone","vehicle_make","vehicle_model","vehicle_year"].map(f => (
                          <td key={f} style={styles.td}>
                            <input style={styles.inlineInput} value={editForm[f]||""}
                              onChange={e => setEditForm(p => ({...p,[f]:e.target.value}))}/>
                          </td>
                        ))}
                        <td style={styles.tdDate}>{fmtDate(c.Date_cust_joined)}</td>
                        <td style={styles.tdActions}>
                          <button style={styles.btnSave} onClick={() => handleSaveEdit(c.id)}><SaveIcon/></button>
                          <button style={styles.btnCancel} onClick={cancelEdit}><CancelIcon/></button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td style={styles.tdId} title={c.id}>{c.id}</td>
                        <td style={styles.tdUser}>{c.username}</td>
                        <td style={styles.td}>{c.cust_first_name}</td>
                        <td style={styles.td}>{c.cust_last_name}</td>
                        <td style={styles.td}>{c.cellphone || "—"}</td>
                        <td style={styles.td}>{c.vehicle_make}</td>
                        <td style={styles.td}>{c.vehicle_model}</td>
                        <td style={styles.tdYear}>{c.vehicle_year}</td>
                        <td style={styles.tdDate}>{fmtDate(c.Date_cust_joined)}</td>
                        <td style={styles.tdActions}>
                          <button style={styles.btnEdit} onClick={() => startEdit(c)}><EditIcon/> Edit</button>
                          <button style={styles.btnDelete} onClick={() => setDeleteId(c.id)}><TrashIcon/></button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Customer Modal */}
      {showAdd && (
        <div style={styles.overlay} onClick={e => { if(e.target===e.currentTarget) setShowAdd(false); }}>
          <div style={styles.modal}>
            <div style={styles.modalHeader}>
              <div style={styles.modalTitle}><CarIcon/> Add New Customer</div>
              <button style={styles.modalClose} onClick={() => setShowAdd(false)}>✕</button>
            </div>
            <form onSubmit={handleAdd} style={styles.modalForm}>
              <div style={styles.formGrid}>
                {[
                  ["username","Email Address","email","e.g. jkamau@email.com"],
                  ["cust_first_name","First Name","text","e.g. Johnny"],
                  ["cust_last_name","Last Name","text","e.g. Kamau"],
                  ["cellphone","Cellphone","tel","e.g. +254712345678"],
                  ["vehicle_make","Vehicle Make","text","e.g. Toyota"],
                  ["vehicle_model","Vehicle Model","text","e.g. Probox"],
                  ["vehicle_year","Vehicle Year","number","e.g. 2015"],
                ].map(([field,label,type,ph]) => (
                  <div key={field} style={styles.formGroup}>
                    <label style={styles.label}>{label}</label>
                    <input style={styles.input} type={type} placeholder={ph}
                      value={addForm[field]} onChange={e => setAddForm(p => ({...p,[field]:e.target.value}))}/>
                  </div>
                ))}
              </div>
              {addErr && <p style={styles.errMsg}>{addErr}</p>}
              <div style={styles.modalFooter}>
                <button type="button" style={styles.btnSecondary} onClick={() => setShowAdd(false)}>Cancel</button>
                <button type="submit" style={styles.btnPrimary}><PlusIcon/> Add Customer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirm Modal */}
      {deleteId && (
        <div style={styles.overlay}>
          <div style={{...styles.modal, maxWidth:400}}>
            <div style={styles.modalHeader}>
              <div style={{...styles.modalTitle, color:"#ef4444"}}><TrashIcon/> Confirm Delete</div>
            </div>
            <p style={{color:"#94a3b8", padding:"0 24px 8px"}}>
              Are you sure you want to permanently delete this customer record? This cannot be undone.
            </p>
            <div style={{...styles.modalFooter, padding:"16px 24px 24px"}}>
              <button style={styles.btnSecondary} onClick={() => setDeleteId(null)}>Cancel</button>
              <button style={{...styles.btnPrimary, background:"#ef4444"}} onClick={handleDelete}>Delete</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// STYLES
// ═══════════════════════════════════════════════════════════════
const styles = {
  app:           { minHeight:"100vh", background:"#0a0f1e", fontFamily:"'DM Sans', sans-serif", color:"#e2e8f0" },
  splash:        { display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#0a0f1e" },
  splashInner:   { textAlign:"center" },
  splashLogo:    { width:56, height:56, borderRadius:"50%", background:"linear-gradient(135deg,#f97316,#ea580c)", display:"flex", alignItems:"center", justifyContent:"center", margin:"0 auto 16px", color:"#fff" },
  splashText:    { color:"#64748b", fontSize:14 },
  loginPage:     { minHeight:"100vh", background:"linear-gradient(135deg,#0a0f1e 0%,#0f172a 50%,#0a0f1e 100%)", display:"flex", alignItems:"center", justifyContent:"center" },
  loginCard:     { background:"#0f172a", border:"1px solid #1e293b", borderRadius:20, padding:"48px 40px", width:"100%", maxWidth:420, boxShadow:"0 25px 50px rgba(0,0,0,0.5)" },
  loginLogo:     { textAlign:"center", marginBottom:36 },
  logoCircle:    { width:64, height:64, borderRadius:"50%", background:"linear-gradient(135deg,#f97316,#ea580c)", display:"flex", alignItems:"center", justifyContent:"center", margin:"0 auto 16px", color:"#fff", boxShadow:"0 0 30px rgba(249,115,22,0.35)" },
  loginBrand:    { fontSize:26, fontWeight:700, color:"#f1f5f9", margin:0, letterSpacing:"-0.5px" },
  loginSub:      { color:"#64748b", fontSize:13, marginTop:4 },
  loginForm:     { display:"flex", flexDirection:"column", gap:18 },
  nav:           { background:"#0f172a", borderBottom:"1px solid #1e293b", padding:"14px 32px", display:"flex", alignItems:"center", justifyContent:"space-between", position:"sticky", top:0, zIndex:100 },
  navBrand:      { display:"flex", alignItems:"center", gap:12 },
  navLogoCircle: { width:36, height:36, borderRadius:"50%", background:"linear-gradient(135deg,#f97316,#ea580c)", display:"flex", alignItems:"center", justifyContent:"center", color:"#fff" },
  navTitle:      { fontSize:18, fontWeight:700, color:"#f1f5f9", letterSpacing:"-0.3px" },
  navBadge:      { background:"rgba(249,115,22,0.15)", color:"#f97316", fontSize:11, fontWeight:600, padding:"2px 8px", borderRadius:20, border:"1px solid rgba(249,115,22,0.3)" },
  navRight:      { display:"flex", alignItems:"center", gap:16 },
  navUser:       { color:"#64748b", fontSize:13 },
  btnLogout:     { display:"flex", alignItems:"center", gap:6, background:"transparent", border:"1px solid #334155", color:"#94a3b8", borderRadius:8, padding:"7px 14px", cursor:"pointer", fontSize:13 },
  pageHeader:    { padding:"28px 32px 20px", display:"flex", alignItems:"flex-start", justifyContent:"space-between", flexWrap:"wrap", gap:16 },
  pageTitle:     { fontSize:22, fontWeight:700, color:"#f1f5f9", margin:0, letterSpacing:"-0.5px" },
  pageSub:       { color:"#64748b", fontSize:13, margin:"4px 0 0", display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" },
  clearBtn:      { background:"rgba(249,115,22,0.12)", border:"1px solid rgba(249,115,22,0.3)", color:"#f97316", borderRadius:6, padding:"2px 10px", fontSize:12, cursor:"pointer" },
  headerActions: { display:"flex", alignItems:"center", gap:12 },
  content:       { padding:"0 32px 40px" },
  loadingBox:    { textAlign:"center", padding:80 },
  spinner:       { width:36, height:36, border:"3px solid #1e293b", borderTop:"3px solid #f97316", borderRadius:"50%", animation:"spin 0.8s linear infinite", margin:"0 auto" },
  tableWrap:     { overflowX:"auto", borderRadius:14, border:"1px solid #1e293b" },
  table:         { width:"100%", borderCollapse:"collapse", fontSize:13 },
  th:            { background:"#0f172a", padding:"12px 14px", textAlign:"left", borderBottom:"1px solid #1e293b", verticalAlign:"middle", whiteSpace:"nowrap" },
  tr:            { borderBottom:"1px solid #1e293b", transition:"background .15s", cursor:"default" },
  trEdit:        { borderBottom:"1px solid #1e293b", background:"#1a2744" },
  td:            { padding:"13px 16px", color:"#cbd5e1", verticalAlign:"middle" },
  tdId:          { padding:"13px 16px", color:"#475569", fontSize:11, fontFamily:"'DM Mono',monospace", verticalAlign:"middle", maxWidth:130, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" },
  tdUser:        { padding:"13px 16px", color:"#f97316", fontWeight:600, verticalAlign:"middle", fontFamily:"'DM Mono',monospace" },
  tdYear:        { padding:"13px 16px", color:"#94a3b8", verticalAlign:"middle", textAlign:"center" },
  tdDate:        { padding:"13px 16px", color:"#64748b", fontSize:12, verticalAlign:"middle", whiteSpace:"nowrap" },
  tdActions:     { padding:"10px 16px", verticalAlign:"middle", whiteSpace:"nowrap" },
  emptyCell:     { textAlign:"center", padding:48, color:"#475569" },
  inlineInput:   { background:"#0f172a", border:"1px solid #f97316", color:"#e2e8f0", borderRadius:6, padding:"6px 10px", fontSize:13, width:"100%", outline:"none", minWidth:80 },
  btnPrimary:    { display:"flex", alignItems:"center", gap:7, background:"linear-gradient(135deg,#f97316,#ea580c)", color:"#fff", border:"none", borderRadius:10, padding:"10px 20px", fontSize:13, fontWeight:600, cursor:"pointer", whiteSpace:"nowrap" },
  btnSecondary:  { background:"transparent", border:"1px solid #334155", color:"#94a3b8", borderRadius:10, padding:"10px 18px", fontSize:13, cursor:"pointer" },
  btnEdit:       { display:"inline-flex", alignItems:"center", gap:5, background:"rgba(249,115,22,0.1)", border:"1px solid rgba(249,115,22,0.3)", color:"#f97316", borderRadius:7, padding:"5px 10px", fontSize:12, cursor:"pointer", marginRight:6 },
  btnDelete:     { display:"inline-flex", alignItems:"center", background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", color:"#ef4444", borderRadius:7, padding:"5px 8px", fontSize:12, cursor:"pointer" },
  btnSave:       { display:"inline-flex", alignItems:"center", background:"rgba(34,197,94,0.15)", border:"1px solid rgba(34,197,94,0.35)", color:"#22c55e", borderRadius:7, padding:"5px 8px", cursor:"pointer", marginRight:6 },
  btnCancel:     { display:"inline-flex", alignItems:"center", background:"rgba(100,116,139,0.15)", border:"1px solid #334155", color:"#94a3b8", borderRadius:7, padding:"5px 8px", cursor:"pointer" },
  formGroup:     { display:"flex", flexDirection:"column", gap:6 },
  formGrid:      { display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:4 },
  label:         { fontSize:12, fontWeight:600, color:"#64748b", letterSpacing:"0.04em", textTransform:"uppercase" },
  input:         { background:"#1e293b", border:"1px solid #334155", color:"#e2e8f0", borderRadius:10, padding:"11px 14px", fontSize:14, outline:"none" },
  errMsg:        { color:"#ef4444", fontSize:12, marginTop:2 },
  overlay:       { position:"fixed", inset:0, background:"rgba(0,0,0,0.7)", display:"flex", alignItems:"center", justifyContent:"center", zIndex:200, backdropFilter:"blur(4px)" },
  modal:         { background:"#0f172a", border:"1px solid #1e293b", borderRadius:18, width:"100%", maxWidth:600, boxShadow:"0 25px 60px rgba(0,0,0,0.6)" },
  modalHeader:   { display:"flex", alignItems:"center", justifyContent:"space-between", padding:"22px 24px 18px", borderBottom:"1px solid #1e293b" },
  modalTitle:    { display:"flex", alignItems:"center", gap:8, fontSize:16, fontWeight:700, color:"#f1f5f9" },
  modalClose:    { background:"transparent", border:"none", color:"#64748b", fontSize:18, cursor:"pointer" },
  modalForm:     { padding:"20px 24px 0" },
  modalFooter:   { display:"flex", justifyContent:"flex-end", gap:10, padding:"20px 0 24px" },
  toast:         { position:"fixed", bottom:28, right:28, color:"#fff", borderRadius:12, padding:"13px 22px", fontSize:14, fontWeight:500, zIndex:999, boxShadow:"0 8px 24px rgba(0,0,0,0.4)" },
};
