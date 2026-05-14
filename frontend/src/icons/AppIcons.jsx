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
