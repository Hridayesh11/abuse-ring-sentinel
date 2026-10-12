
import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const { session, loading } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  if (loading) {
    return <div className="auth-loading">Checking session...</div>;
  }

  if (session) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage('');
    setBusy(true);

    try {
      if (isSignup) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: window.location.origin,
          },
        });

        if (error) throw error;

        setMessage(
          data.session
            ? 'Account created successfully.'
            : 'Account created. Check your email to confirm your account.',
        );
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) throw error;
      }
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Authentication failed. Please try again.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <ShieldAlert size={30} />
          <div>
            <h1>Abuse Ring Sentinel</h1>
            <p>AI Risk Manager · Track 02</p>
          </div>
        </div>

        <h2>{isSignup ? 'Create your account' : 'Welcome back'}</h2>
        <p className="auth-subtitle">
          {isSignup
            ? 'Register to access the investigation dashboard.'
            : 'Sign in to access the investigation dashboard.'}
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            minLength={isSignup ? 8 : undefined}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={isSignup ? 'At least 8 characters' : 'Your password'}
            required
          />

          <button type="submit" disabled={busy}>
            {busy
              ? 'Please wait...'
              : isSignup
                ? 'Create account'
                : 'Sign in'}
          </button>
        </form>

        {message && (
          <p className="auth-message" role="status">
            {message}
          </p>
        )}

        <p className="auth-switch">
          {isSignup ? 'Already registered?' : 'New to Abuse Ring Sentinel?'}{' '}
          <button
            type="button"
            className="auth-link"
            onClick={() => {
              setIsSignup(!isSignup);
              setMessage('');
            }}
          >
            {isSignup ? 'Sign in' : 'Create an account'}
          </button>
        </p>
      </section>
    </main>
  );
}
