import { useState } from "react";
import "./App.css";

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [expandedFiles, setExpandedFiles] = useState({});

  const analyzeRepository = async () => {
    if (!repositoryUrl.trim()) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setExpandedFiles({});

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/repositories/review",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repository_url: repositoryUrl,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Repository analysis failed."
        );
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleFile = (index) => {
    setExpandedFiles((current) => ({
      ...current,
      [index]: !current[index],
    }));
  };

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-content">
          <p className="eyebrow">AI-POWERED DEVELOPER TOOL</p>

          <h1>AI Code Review Agent</h1>

          <p className="hero-description">
            Analyze GitHub repositories with AI and surface
            code quality, security, and maintainability issues.
          </p>
        </div>
      </header>

      <main className="container">
        <section className="panel analyzer-panel">
          <div>
            <p className="section-label">REPOSITORY ANALYSIS</p>
            <h2>Review a GitHub repository</h2>
            <p className="muted">
              Paste a public GitHub URL and let Qwen2.5-Coder
              analyze the source code.
            </p>
          </div>

          <div className="input-group">
            <input
              type="url"
              placeholder="https://github.com/username/repository"
              value={repositoryUrl}
              onChange={(event) =>
                setRepositoryUrl(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter" && !loading) {
                  analyzeRepository();
                }
              }}
            />

            <button
              onClick={analyzeRepository}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze Repository"}
            </button>
          </div>

          {loading && (
            <div className="loading-box">
              <div className="spinner" />
              <div>
                <strong>AI review in progress</strong>
                <p>
                  Cloning, scanning, and reviewing source files.
                  This may take a few minutes.
                </p>
              </div>
            </div>
          )}

          {error && <div className="error">{error}</div>}
        </section>

        {result && (
          <>
            <section className="results-header">
              <div>
                <p className="section-label">ANALYSIS COMPLETE</p>
                <h2>{result.repository_name}</h2>
                <p className="repo-url">
                  {result.repository_url}
                </p>
              </div>

              <div className="score-card">
                <span>Health Score</span>
                <strong>{result.repository_score}</strong>
                <small>/100</small>
              </div>
            </section>

            <section className="severity-grid">
              <div className="metric-card">
                <span>Files Reviewed</span>
                <strong>
                  {result.total_files_reviewed}
                </strong>
              </div>

              <div className="metric-card">
                <span>Total Issues</span>
                <strong>{result.total_issues}</strong>
              </div>

              <div className="metric-card critical">
                <span>Critical</span>
                <strong>
                  {result.severity_counts.critical}
                </strong>
              </div>

              <div className="metric-card high">
                <span>High</span>
                <strong>
                  {result.severity_counts.high}
                </strong>
              </div>

              <div className="metric-card medium">
                <span>Medium</span>
                <strong>
                  {result.severity_counts.medium}
                </strong>
              </div>

              <div className="metric-card low">
                <span>Low</span>
                <strong>
                  {result.severity_counts.low}
                </strong>
              </div>
            </section>

            <section className="summary-grid">
              <article className="panel">
                <p className="section-label">AI SUMMARY</p>
                <h3>Overall Quality</h3>
                <p>
                  {result.repository_summary.overall_quality}
                </p>
              </article>

              <article className="panel">
                <p className="section-label">SECURITY</p>
                <h3>Security Assessment</h3>
                <p>
                  {
                    result.repository_summary
                      .security_assessment
                  }
                </p>
              </article>

              <article className="panel">
                <p className="section-label">MAINTAINABILITY</p>
                <h3>Maintainability Assessment</h3>
                <p>
                  {
                    result.repository_summary
                      .maintainability_assessment
                  }
                </p>
              </article>
            </section>

            <section className="two-column">
              <article className="panel">
                <p className="section-label">PRIORITY</p>
                <h3>Top Risks</h3>

                {result.repository_summary.top_risks.length === 0 ? (
                  <p className="muted">
                    No major repository-level risks identified.
                  </p>
                ) : (
                  <ul className="recommendation-list">
                    {result.repository_summary.top_risks.map(
                      (risk, index) => (
                        <li key={index}>{risk}</li>
                      )
                    )}
                  </ul>
                )}
              </article>

              <article className="panel">
                <p className="section-label">NEXT ACTIONS</p>
                <h3>Top Recommendations</h3>

                <ul className="recommendation-list">
                  {result.repository_summary.top_recommendations.map(
                    (recommendation, index) => (
                      <li key={index}>{recommendation}</li>
                    )
                  )}
                </ul>
              </article>
            </section>

            <section className="panel file-section">
              <div className="file-section-heading">
                <div>
                  <p className="section-label">
                    DETAILED FINDINGS
                  </p>
                  <h3>File-by-File Review</h3>
                </div>

                <span>
                  {result.files.length} files
                </span>
              </div>

              <div className="file-list">
                {result.files.map((file, fileIndex) => (
                  <article
                    className="file-card"
                    key={`${file.path}-${fileIndex}`}
                  >
                    <button
                      className="file-toggle"
                      onClick={() =>
                        toggleFile(fileIndex)
                      }
                    >
                      <div>
                        <strong>{file.path}</strong>
                        <span>{file.language}</span>
                      </div>

                      <div className="file-meta">
                        <span>
                          {file.issues.length}{" "}
                          {file.issues.length === 1
                            ? "issue"
                            : "issues"}
                        </span>

                        <span>
                          {expandedFiles[fileIndex]
                            ? "−"
                            : "+"}
                        </span>
                      </div>
                    </button>

                    {expandedFiles[fileIndex] && (
                      <div className="file-content">
                        <div className="file-summary">
                          <strong>AI Summary</strong>
                          <p>{file.summary}</p>
                        </div>

                        {file.issues.length === 0 ? (
                          <div className="clean-file">
                            No issues detected in this file.
                          </div>
                        ) : (
                          <div className="issue-list">
                            {file.issues.map(
                              (issue, issueIndex) => (
                                <div
                                  className="issue-card"
                                  key={issueIndex}
                                >
                                  <div className="issue-heading">
                                    <span
                                      className={`severity-badge ${issue.severity.toLowerCase()}`}
                                    >
                                      {issue.severity}
                                    </span>

                                    <span className="category">
                                      {issue.category}
                                    </span>
                                  </div>

                                  <h4>{issue.title}</h4>

                                  {issue.line && (
                                    <p className="line-number">
                                      Line: {issue.line}
                                    </p>
                                  )}

                                  <p>{issue.description}</p>

                                  <div className="recommendation">
                                    <strong>
                                      Recommended Fix
                                    </strong>
                                    <p>
                                      {issue.recommendation}
                                    </p>
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;