import { Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth";
import Sky from "./Sky";
import LoginPage from "./pages/LoginPage";
import TaskPage from "./pages/TaskPage";
import TasksPage from "./pages/TasksPage";

export default function App() {
  return (
    <>
      <Sky />
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/tasks"
          element={
            <RequireAuth>
              <TasksPage />
            </RequireAuth>
          }
        />
        <Route
          path="/tasks/new"
          element={
            <RequireAuth>
              <TaskPage isNew />
            </RequireAuth>
          }
        />
        <Route
          path="/tasks/:id"
          element={
            <RequireAuth>
              <TaskPage />
            </RequireAuth>
          }
        />
      </Routes>
    </>
  );
}
