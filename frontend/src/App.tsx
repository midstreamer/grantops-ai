import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { GrantSearchPage } from "./pages/GrantSearch";
import { OpportunitiesPage } from "./pages/Opportunities";
import { OpportunityDetailPage } from "./pages/OpportunityDetail";
import { ResearchProfilePage } from "./pages/ResearchProfile";
import { AgentWorkflowPage } from "./pages/AgentWorkflow";
import { ScheduledSearchesPage } from "./pages/ScheduledSearches";
import { WeeklyReportsPage } from "./pages/WeeklyReports";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="nav">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/research-profile"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Research Profile
          </NavLink>
          <NavLink
            to="/opportunities"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Opportunities
          </NavLink>
          <NavLink
            to="/grant-search"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Grant Search
          </NavLink>
          <NavLink
            to="/agent-workflow"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Agent Workflow
          </NavLink>
          <NavLink
            to="/scheduled-searches"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Scheduled Searches
          </NavLink>
          <NavLink
            to="/weekly-reports"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Weekly Reports
          </NavLink>
        </nav>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/research-profile" element={<ResearchProfilePage />} />
          <Route path="/opportunities" element={<OpportunitiesPage />} />
          <Route path="/opportunities/:id" element={<OpportunityDetailPage />} />
          <Route path="/grant-search" element={<GrantSearchPage />} />
          <Route path="/agent-workflow" element={<AgentWorkflowPage />} />
          <Route path="/scheduled-searches" element={<ScheduledSearchesPage />} />
          <Route path="/weekly-reports" element={<WeeklyReportsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
