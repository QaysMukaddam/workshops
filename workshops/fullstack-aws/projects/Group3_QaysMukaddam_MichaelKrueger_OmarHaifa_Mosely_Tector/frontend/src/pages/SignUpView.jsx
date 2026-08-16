import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

// registerUser calls POST /register. loginUser calls POST /login — we
// chain them so a new user is immediately logged in after signing up.
import { registerUser, loginUser } from '../api/api';

import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import Button from '../components/Button';

export default function SignUpView() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Which role the new account should have. Defaults to MEMBER so
  // creating an ADMIN account requires an explicit, deliberate choice.
  const [role, setRole] = useState('MEMBER');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Create the account with whichever role was selected.
      await registerUser(username, password, role);
      // Immediately log the new account in, so the user doesn't have to
      // re-type their credentials on a separate login screen.
      const response = await loginUser(username, password);
      login(response.access_token);
      navigate('/dashboard');
    } catch (err) {
      // Covers both "username already taken" and any other backend error.
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-white mb-6 text-center">
          Create an account
        </h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
          />

          {/* Role picker: two toggle buttons instead of a plain dropdown,
              so the "which am I signing up as" choice is visually clear. */}
          <div className="flex flex-col gap-2">
            <label className="text-gray-400 text-sm">I am registering as:</label>
            <div className="flex gap-3">
              {/* type="button" (not "submit") so clicking this doesn't
                  submit the form early — it only updates the role state. */}
              <button
                type="button"
                onClick={() => setRole('MEMBER')}
                className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-all ${
                  role === 'MEMBER'
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-white/10 text-gray-400'
                }`}
              >
                Organization Member
              </button>
              <button
                type="button"
                onClick={() => setRole('ADMIN')}
                className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-all ${
                  role === 'ADMIN'
                    ? 'border-accent-2 bg-accent-2/10 text-accent-2'
                    : 'border-white/10 text-gray-400'
                }`}
              >
                Organization Admin
              </button>
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <Button type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Sign Up'}
          </Button>
        </form>

        <p className="text-gray-400 text-sm text-center mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}