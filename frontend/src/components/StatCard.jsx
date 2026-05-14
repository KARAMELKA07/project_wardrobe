export default function StatCard({ label, value, helpText }) {
  return (
    <article className="stat-card">
      <p className="stat-card-label">{label}</p>
      <h3 className="stat-card-value">{value}</h3>
      {helpText ? <p className="stat-card-help">{helpText}</p> : null}
    </article>
  );
}
