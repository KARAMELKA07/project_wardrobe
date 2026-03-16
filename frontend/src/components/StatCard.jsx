export default function StatCard({ label, value, helpText }) {
  return (
    <article className="stat-card">
      <p className="eyebrow">{label}</p>
      <h3>{value}</h3>
      {helpText ? <p className="muted-text">{helpText}</p> : null}
    </article>
  );
}
