"use client";

import { useEffect } from "react";

type ErrorPageProps = Readonly<{
  error: Error & { digest?: string };
  reset: () => void;
}>;

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="shell" role="alert">
      <p className="eyebrow">Margin</p>
      <h1>Something interrupted this page.</h1>
      <p className="lede">Try loading the reading space again.</p>
      <button className="retry" type="button" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
