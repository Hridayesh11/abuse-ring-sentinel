import { Routes, Route, NavLink } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, Search, Cpu, Activity } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Investigation from './pages/Investigation';

function App() {
  return (
    <div className="app-container">
      <aside className="sidebar">
        {/* Brand Header */}
        <div className="sidebar-header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.375rem', paddingBottom: '1.25rem' }}>
          <div className="flex items-center gap-2">
            <div style={{
              width: 32, height: 32, borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(239,68,68,0.3) 0%, rgba(239,68,68,0.15) 100%)',
              border: '1px solid rgba(239,68,68,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ShieldAlert size={18} style={{ color: 'var(--color-critical)' }} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', lineHeight: 1.2 }}>Abuse Ring Sentinel</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 400 }}>AI Risk Manager</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginTop: '0.375rem' }}>
            <span style={{
              fontSize: '0.65rem', fontWeight: 600, padding: '0.15rem 0.5rem',
              borderRadius: '999px', background: 'rgba(59,130,246,0.12)',
              border: '1px solid rgba(59,130,246,0.25)', color: '#93c5fd',
              textTransform: 'uppercase', letterSpacing: '0.06em'
            }}>Razorpay Buildathon</span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Track 02</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav" style={{ flexDirection: 'column' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
            <p style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0.5rem 1rem 0.25rem' }}>
              Navigation
            </p>

            <NavLink 
              to="/" 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end
            >
              <LayoutDashboard size={16} />
              Executive Dashboard
            </NavLink>

            <NavLink 
              to="/investigation" 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Search size={16} />
              Forensic Investigation
            </NavLink>
          </div>

          {/* Engine Status Footer */}
          <div style={{
            padding: '1rem',
            borderTop: '1px solid var(--border-color)',
            marginTop: '0.5rem',
          }}>
            <div style={{ marginBottom: '0.625rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#22c55e', boxShadow: '0 0 6px #22c55e', flexShrink: 0 }} />
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>ML Engine Active</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', paddingLeft: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Cpu size={10} style={{ color: 'var(--text-muted)' }} />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>XGBoost + Graph Features</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Activity size={10} style={{ color: 'var(--text-muted)' }} />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>1,000 accounts monitored</span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textAlign: 'center', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle, #152030)' }}>
              v1.0.0 · Graph Entity Sentinel
            </div>
          </div>
        </nav>
      </aside>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/investigation" element={<Investigation />} />
          <Route path="/investigation/:accountId" element={<Investigation />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
