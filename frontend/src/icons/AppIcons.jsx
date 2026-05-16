function buildClassName(baseClassName, className) {
  return className ? `${baseClassName} ${className}` : baseClassName;
}

export function PencilIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M9 20H4V15L15 4L20 9L9 20Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13 6L18 11"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 20H20"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function TrashIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M5 7H19"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M9 7V5.5C9 4.67 9.67 4 10.5 4H13.5C14.33 4 15 4.67 15 5.5V7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8 7L8.7 18.2C8.75 18.96 9.38 19.55 10.15 19.55H13.85C14.62 19.55 15.25 18.96 15.3 18.2L16 7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 10.5V15.5M14 10.5V15.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function CloseIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M6 6L18 18M6 18L18 6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ArrowLeftIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M20 12H6"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
      <path
        d="M11 7L6 12L11 17"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ArrowRightIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M4 12H18"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
      <path
        d="M13 7L18 12L13 17"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function FlipIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M8 7H18"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M15 4L18 7L15 10"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 17H6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M9 14L6 17L9 20"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function HeartIcon({ className = "", filled = false }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M12 20C10 19.2 3.5 14.5 3.5 8.8C3.5 5.88 5.88 3.5 8.8 3.5C10.58 3.5 11.92 4.34 12.75 5.54C12.89 5.74 13.11 5.74 13.25 5.54C14.08 4.34 15.42 3.5 17.2 3.5C20.12 3.5 22.5 5.88 22.5 8.8C22.5 14.5 16 19.2 14 20L13 20.35L12 20Z"
        fill={filled ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CloudIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M7.5 18.5H16.5C19.26 18.5 21.5 16.26 21.5 13.5C21.5 10.86 19.45 8.71 16.86 8.52C16.16 5.92 13.79 4 11 4C7.66 4 4.93 6.64 4.79 9.95C2.91 10.65 1.5 12.46 1.5 14.6C1.5 16.76 3.24 18.5 5.4 18.5H7.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SunIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="4.25"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path d="M12 2.5V5.25M12 18.75V21.5M21.5 12H18.75M5.25 12H2.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M18.72 5.28L16.78 7.22M7.22 16.78L5.28 18.72M18.72 18.72L16.78 16.78M7.22 7.22L5.28 5.28" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function RainIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M7.5 15.5H16.5C19.26 15.5 21.5 13.26 21.5 10.5C21.5 7.86 19.45 5.71 16.86 5.52C16.16 2.92 13.79 1 11 1C7.66 1 4.93 3.64 4.79 6.95C2.91 7.65 1.5 9.46 1.5 11.6C1.5 13.76 3.24 15.5 5.4 15.5H7.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M8 18L7 21M12 18L11 21M16 18L15 21" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function SnowIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path
        d="M7.5 14.75H16.5C19.26 14.75 21.5 12.51 21.5 9.75C21.5 7.11 19.45 4.96 16.86 4.77C16.16 2.17 13.79 0.25 11 0.25C7.66 0.25 4.93 2.89 4.79 6.2C2.91 6.9 1.5 8.71 1.5 10.85C1.5 13.01 3.24 14.75 5.4 14.75H7.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M9 18.25H15M12 15.25V21.25M9.75 16.5L14.25 20M14.25 16.5L9.75 20" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function WindIcon({ className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={buildClassName("ui-icon", className)}
      fill="none"
    >
      <path d="M3 9.5H15C17.49 9.5 19.5 7.49 19.5 5C19.5 4.17 18.83 3.5 18 3.5C17.17 3.5 16.5 4.17 16.5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 14.5H19C20.38 14.5 21.5 15.62 21.5 17C21.5 18.38 20.38 19.5 19 19.5C17.62 19.5 16.5 18.38 16.5 17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
