import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listTasks } from "../api";
import { useAuth } from "../auth";

export default function TasksPage() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const rows = await listTasks(token);
        if (!cancelled) setTasks(rows);
      } catch (err) {
        if (err.status === 401) {
          logout();
          navigate("/");
          return;
        }
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token, logout, navigate]);

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Task Gamifi</p>
          <h1>Your skyboard</h1>
        </div>
        <div className="topbar-actions">
          <span className="muted">{user?.email}</span>
          <button type="button" className="ghost" onClick={() => { logout(); navigate("/"); }}>
            Log out
          </button>
          <Link className="primary" to="/tasks/new">
            + New task
          </Link>
        </div>
      </header>

      {loading ? <p className="muted">Loading your board...</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {!loading && tasks.length === 0 ? (
        <div className="panel empty">
          <h2>Wide open sky</h2>
          <p>Start a new task and the planner will turn it into levels, points, and rewards.</p>
          <Link className="primary" to="/tasks/new">
            + New task
          </Link>
        </div>
      ) : (
        <div className="card-grid">
          {tasks.map((task) => (
            <Link key={task.id} className="task-card" to={`/tasks/${task.id}`}>
              <p className="eyebrow">{task.category || "Path"}</p>
              <h2>{task.title}</h2>
              <p className="muted clamp">{task.compiled?.summary || task.raw_data}</p>
              <div className="meta">
                <span>{task.total_points} pts</span>
                <span>{task.difficulty_score ?? 0}/100</span>
                <span>{task.compiled?.levels?.length || 0} levels</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
