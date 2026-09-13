import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getTask, ingestTask } from "../api";
import { useAuth } from "../auth";

export default function TaskPage({ isNew = false }) {
  const { id } = useParams();
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [rawData, setRawData] = useState("");
  const [topic, setTopic] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!isNew);
  const [planning, setPlanning] = useState(false);

  useEffect(() => {
    if (isNew) return undefined;
    let cancelled = false;
    async function load() {
      try {
        const row = await getTask(token, id);
        if (!cancelled) setTask(row);
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
  }, [id, isNew, token, logout, navigate]);

  async function onPlan(event) {
    event.preventDefault();
    setError("");
    setPlanning(true);
    try {
      const created = await ingestTask(token, { raw_data: rawData, topic });
      navigate(`/tasks/${created.id}`, { replace: true });
    } catch (err) {
      if (err.status === 401) {
        logout();
        navigate("/");
        return;
      }
      setError(err.message);
    } finally {
      setPlanning(false);
    }
  }

  const compiled = task?.compiled || {};
  const levels = compiled.levels || [];

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <Link className="back" to="/tasks">
            ← Tasks
          </Link>
          <h1>{isNew ? "New task" : compiled.title || task?.title || "Task"}</h1>
        </div>
      </header>

      {isNew ? (
        <form className="panel stack" onSubmit={onPlan}>
          <p className="lede">
            Drop in messy notes if you have them. If you leave this blank, the planner will
            chart a starter path across the sky for you.
          </p>
          <label>
            Optional topic
            <input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Learn Rust, ship a side project..."
            />
          </label>
          <label>
            Raw material
            <textarea
              rows={10}
              value={rawData}
              onChange={(event) => setRawData(event.target.value)}
              placeholder="Syllabus, brain dump, goals, constraints..."
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button className="primary" type="submit" disabled={planning}>
            {planning ? "Planning with AI..." : "Plan and save"}
          </button>
          {planning ? (
            <p className="muted">
              Structure → levels → points → review. This is stored in your timeline table when it
              finishes.
            </p>
          ) : null}
        </form>
      ) : null}

      {!isNew && loading ? <p className="muted">Loading task from the database...</p> : null}
      {!isNew && error ? <p className="error">{error}</p> : null}

      {!isNew && task ? (
        <div className="stack">
          <div className="panel">
            <p className="eyebrow">{compiled.category || task.category}</p>
            <p className="lede">{compiled.summary}</p>
            <div className="meta">
              <span>{task.total_points} pts</span>
              <span>{levels.length} levels</span>
              <span>{compiled.approved ? "Reviewed" : "Needs review"}</span>
            </div>
            {compiled.review_notes ? (
              <p className="muted">{compiled.review_notes}</p>
            ) : null}
          </div>
          {levels.map((level) => (
            <section key={level.level_number} className="panel level">
              <div className="level-head">
                <h2>
                  Level {level.level_number}: {level.name}
                </h2>
                <span className="pill">{level.difficulty}</span>
              </div>
              <p>{level.objective}</p>
              <p className="muted">
                {level.level_points} pts · {level.level_reward}
              </p>
              <ul className="task-list">
                {(level.tasks || []).map((item) => (
                  <li key={`${level.level_number}-${item.title}`}>
                    <strong>{item.title}</strong>
                    <span>{item.description}</span>
                    <em>
                      {item.difficulty} · {item.points} pts · {item.reward}
                    </em>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      ) : null}
    </div>
  );
}
