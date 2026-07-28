import { useState } from "react";
import "./App.css";

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const analyzeRepository = async () => {
    if (!repositoryUrl.trim()) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

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

  return (
    <div className="app">
      <header>
        <h1>AI Code Review Agent</h1>
        <p>
          Analyze a GitHub repository using AI and discover
          security, quality, and maintainability issues.
        </p>
      </header>

      <main>
        <section className="analyzer">
          <h2>Analyze Repository</h2>

          <div className="input-group">
            <input
              type="url"
              placeholder="https://github.com/username/repository"
              value={repositoryUrl}
              onChange={(event) =>
                setRepositoryUrl(event.target.value)
              }
            />

            <button
              onClick={analyzeRepository}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze Repository"}
            </button>
          </div>

          {loading && (
            <p className="loading">
              AI is reviewing the repository. This may take
              a few minutes...
            </p>
          )}

          {error && (
            <div className="error">
              {error}
            </div>
          )}
        </section>

        {result && (
          <section className="results">
            <h2>{result.repository_name}</h2>

            <div className="score-card">
              <span>Repository Health Score</span>
              <strong>{result.repository_score}/100</strong>
            </div>

            <div className="stats">
              <div>
                <strong>
                  {result.total_files_reviewed}
                </strong>
                <span>Files Reviewed</span>
              </div>

              <div>
                <strong>{result.total_issues}</strong>
                <span>Total Issues</span>
              </div>

              <div>
                <strong>
                  {result.severity_counts.critical}
                </strong>
                <span>Critical</span>
              </div>

              <div>
                <strong>
                  {result.severity_counts.high}
                </strong>
                <span>High</span>
              </div>

              <div>
                <strong>
                  {result.severity_counts.medium}
                </strong>
                <span>Medium</span>
              </div>

              <div>
                <strong>
                  {result.severity_counts.low}
                </strong>
                <span>Low</span>
              </div>
            </div>

            <div className="summary">
              <h3>AI Repository Summary</h3>

              <h4>Overall Quality</h4>
              <p>
                {result.repository_summary.overall_quality}
              </p>

              <h4>Security Assessment</h4>
              <p>
                {
                  result.repository_summary
                    .security_assessment
                }
              </p>

              <h4>Maintainability</h4>
              <p>
                {
                  result.repository_summary
                    .maintainability_assessment
                }
              </p>

              <h4>Top Recommendations</h4>

              <ul>
                {result.repository_summary.top_recommendations.map(
                  (recommendation, index) => (
                    <li key={index}>{recommendation}</li>
                  )
                )}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;