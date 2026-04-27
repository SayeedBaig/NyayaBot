import React from "react";
import LocationCard from "./LocationCard";

const formatItem = (item) => {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") {
    return item.title || item.name || item.text || item.description || JSON.stringify(item);
  }
  return String(item);
};

const ResultSection = ({ title, items }) => {
  if (!items || items.length === 0) return null;

  return (
    <section className="result-section">
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{formatItem(item)}</li>
        ))}
      </ul>
    </section>
  );
};

const ResultPanel = ({
  summary,
  rights,
  law,
  steps,
  documents,
  locations,
  onGenerateDocument,
  onViewLocations,
  onAskAnother,
}) => {
  const hasLocations = locations && locations.length > 0;

  return (
    <section className="result-panel" aria-label="Structured legal guidance">
      <div className="result-header">
        <p className="section-kicker">Legal Guidance</p>
        <h2>Your action plan</h2>
        <button className="action-button primary-action result-header-action" onClick={onGenerateDocument}>
          Generate Complaint Letter
        </button>
      </div>

      {summary && (
        <section className="result-section summary-section">
          <h3>Summary</h3>
          <p>{summary}</p>
        </section>
      )}

      <div className="result-grid">
        <ResultSection title="Your Rights" items={rights} />
        <ResultSection title="Applicable Law" items={law} />
        <ResultSection title="Steps to Take" items={steps} />
        <ResultSection title="Required Documents" items={documents} />
      </div>

      {hasLocations && (
        <section className="result-section locations-section" id="nearby-offices">
          <h3>Nearby Offices</h3>
          <div className="result-locations">
            {locations.map((location, index) => (
              <LocationCard key={`${location.name || "office"}-${index}`} {...location} />
            ))}
          </div>
        </section>
      )}

      <div className="result-actions">
        <button className="action-button primary-action" onClick={onGenerateDocument}>
          Download Complaint Letter
        </button>
        <button className="action-button" onClick={onViewLocations} disabled={!hasLocations}>
          View Nearby Offices
        </button>
        <button className="action-button" onClick={onAskAnother}>
          Ask Another Question
        </button>
      </div>
    </section>
  );
};

export default ResultPanel;
