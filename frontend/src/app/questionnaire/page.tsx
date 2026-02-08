"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Typy ──

interface FollowupField {
  key: string;
  label: string;
  type: "text" | "select";
  options?: string[];
}

interface Question {
  key: string;
  text: string;
  type: string;
  followup?: {
    condition: string;
    fields: FollowupField[];
  };
  risk_hint: string;
  ai_act_article: string;
}

interface Section {
  id: string;
  title: string;
  description: string;
  questions: Question[];
}

interface Answer {
  question_key: string;
  section: string;
  answer: "yes" | "no" | "unknown" | "";
  details: Record<string, string>;
  tool_name: string;
}

interface Recommendation {
  question_key: string;
  tool_name: string;
  risk_level: string;
  ai_act_article: string;
  recommendation: string;
  priority: string;
}

interface AnalysisResult {
  total_answers: number;
  ai_systems_declared: number;
  risk_breakdown: Record<string, number>;
  recommendations: Recommendation[];
}

// ── Pomocné komponenty ──

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    limited: "bg-yellow-100 text-yellow-800",
    minimal: "bg-green-100 text-green-800",
  };
  const labels: Record<string, string> = {
    high: "🔴 Vysoké",
    limited: "🟡 Omezené",
    minimal: "🟢 Minimální",
  };
  return (
    <span className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${colors[level] || "bg-gray-100 text-gray-800"}`}>
      {labels[level] || level}
    </span>
  );
}

function ProgressBar({ current, total }: { current: number; total: number }) {
  const pct = Math.round((current / total) * 100);
  return (
    <div className="mb-6">
      <div className="flex justify-between text-sm text-gray-500 mb-1">
        <span>Sekce {current} z {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Hlavní komponenta ──

export default function QuestionnairePage() {
  const [sections, setSections] = useState<Section[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);

  // Načíst strukturu dotazníku
  useEffect(() => {
    fetch(`${API_URL}/api/questionnaire/structure`)
      .then((r) => r.json())
      .then((data) => {
        setSections(data.sections);
        // Inicializovat odpovědi
        const init: Record<string, Answer> = {};
        for (const section of data.sections) {
          for (const q of section.questions) {
            init[q.key] = {
              question_key: q.key,
              section: section.id,
              answer: "",
              details: {},
              tool_name: "",
            };
          }
        }
        setAnswers(init);
        setLoading(false);
      })
      .catch((e) => {
        setError("Nepodařilo se načíst dotazník.");
        setLoading(false);
      });

    // Pokusit se načíst company_id a scan_id z URL params
    const params = new URLSearchParams(window.location.search);
    if (params.get("company_id")) setCompanyId(params.get("company_id"));
    if (params.get("scan_id")) setScanId(params.get("scan_id"));
  }, []);

  // Handler odpovědi
  const setAnswer = (key: string, value: "yes" | "no" | "unknown") => {
    setAnswers((prev) => ({
      ...prev,
      [key]: { ...prev[key], answer: value },
    }));
  };

  // Handler followup polí
  const setDetail = (questionKey: string, fieldKey: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionKey]: {
        ...prev[questionKey],
        details: { ...prev[questionKey].details, [fieldKey]: value },
        // Pokud je to tool_name pole, uložit i do tool_name
        tool_name: fieldKey.endsWith("tool_name") || fieldKey.endsWith("_tool")
          ? value
          : prev[questionKey].tool_name,
      },
    }));
  };

  // Odeslání dotazníku
  const handleSubmit = async () => {
    if (!companyId) {
      setError("Chybí company_id. Nejdřív spusťte sken webu na stránce /scan.");
      return;
    }

    setSubmitting(true);
    setError(null);

    // Filtrovat jen zodpovězené otázky
    const answeredList = Object.values(answers)
      .filter((a) => a.answer !== "")
      .map((a) => ({
        question_key: a.question_key,
        section: a.section,
        answer: a.answer,
        details: Object.keys(a.details).length > 0 ? a.details : null,
        tool_name: a.tool_name || null,
      }));

    try {
      const res = await fetch(`${API_URL}/api/questionnaire/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId,
          scan_id: scanId,
          answers: answeredList,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Chyba serveru" }));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data.analysis);
      setCurrentStep(sections.length); // Přesunout na výsledky
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Renderování ──

  if (loading) {
    return (
      <section className="py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-500">Načítám dotazník...</p>
        </div>
      </section>
    );
  }

  // Výsledky po odeslání
  if (result) {
    return (
      <section className="py-12">
        <div className="mx-auto max-w-3xl px-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Výsledky dotazníku</h1>
          <p className="text-gray-500 mb-8">Analýza vašich interních AI systémů</p>

          {/* Souhrn */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-blue-600">{result.ai_systems_declared}</div>
                <div className="text-sm text-gray-500">AI systémů deklarováno</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-red-600">{result.risk_breakdown.high || 0}</div>
                <div className="text-sm text-gray-500">Vysoce rizikových</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-yellow-600">{result.risk_breakdown.limited || 0}</div>
                <div className="text-sm text-gray-500">Omezené riziko</div>
              </div>
            </div>
          </div>

          {/* Doporučení */}
          {result.recommendations.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h2 className="text-xl font-bold mb-4">🎯 Doporučení ke compliance</h2>
              <div className="space-y-4">
                {result.recommendations.map((rec, i) => (
                  <div key={i} className="border-l-4 pl-4 py-2" style={{
                    borderColor: rec.risk_level === "high" ? "#ef4444" : rec.risk_level === "limited" ? "#eab308" : "#22c55e"
                  }}>
                    <div className="flex items-center gap-2 mb-1">
                      <RiskBadge level={rec.risk_level} />
                      <span className="font-semibold">{rec.tool_name}</span>
                      <span className="text-xs text-gray-400">{rec.ai_act_article}</span>
                    </div>
                    <p className="text-sm text-gray-700">{rec.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CTA */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl p-6 text-center">
            <h3 className="text-lg font-bold mb-2">🛡️ Chcete kompletní compliance report?</h3>
            <p className="text-sm text-gray-600 mb-4">
              Kombinujeme výsledky skenu webu s vaším dotazníkem pro úplný přehled.
            </p>
            {scanId ? (
              <a
                href={`${API_URL}/api/scan/${scanId}/report`}
                target="_blank"
                className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                📄 Stáhnout kompletní report
              </a>
            ) : (
              <a
                href="/scan"
                className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                🔍 Nejdřív naskenovat web
              </a>
            )}
          </div>
        </div>
      </section>
    );
  }

  // Wizard — kroky dotazníku
  const section = sections[currentStep];
  const isLastStep = currentStep === sections.length - 1;
  const allCurrentAnswered = section
    ? section.questions.every((q) => answers[q.key]?.answer !== "")
    : false;

  return (
    <section className="py-12">
      <div className="mx-auto max-w-3xl px-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📝 AI Compliance Dotazník</h1>
        <p className="text-gray-500 mb-6">
          Pomůže nám odhalit interní AI systémy, které automatický skener nevidí.
          Trvá cca 5 minut.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            ❌ {error}
          </div>
        )}

        {/* Company ID input pokud chybí */}
        {!companyId && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-yellow-800 mb-2">
              💡 Pro uložení odpovědí potřebujeme ID firmy. Nejdřív{" "}
              <a href="/scan" className="underline font-semibold">naskenujte web</a>,
              pak se sem vraťte s parametrem ?company_id=...
            </p>
            <input
              type="text"
              placeholder="Nebo zadejte company_id ručně..."
              className="w-full mt-2 px-3 py-2 border rounded-lg text-sm"
              onChange={(e) => setCompanyId(e.target.value || null)}
            />
          </div>
        )}

        {/* Progress bar */}
        <ProgressBar current={currentStep + 1} total={sections.length} />

        {/* Aktuální sekce */}
        {section && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-1">{section.title}</h2>
            <p className="text-sm text-gray-500 mb-6">{section.description}</p>

            <div className="space-y-6">
              {section.questions.map((q) => {
                const ans = answers[q.key];
                return (
                  <div key={q.key} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <p className="font-medium text-gray-800">{q.text}</p>
                      <RiskBadge level={q.risk_hint} />
                    </div>

                    {/* Ano / Ne / Nevím tlačítka */}
                    <div className="flex gap-2 mb-3">
                      {(["yes", "no", "unknown"] as const).map((val) => {
                        const labels = { yes: "✅ Ano", no: "❌ Ne", unknown: "❓ Nevím" };
                        const isSelected = ans?.answer === val;
                        return (
                          <button
                            key={val}
                            onClick={() => setAnswer(q.key, val)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                              isSelected
                                ? "bg-blue-600 text-white shadow-md"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                            }`}
                          >
                            {labels[val]}
                          </button>
                        );
                      })}
                    </div>

                    {/* AI Act reference */}
                    <p className="text-xs text-gray-400 mb-2">📜 {q.ai_act_article}</p>

                    {/* Followup otázky při "Ano" */}
                    {ans?.answer === "yes" && q.followup && (
                      <div className="mt-3 pl-4 border-l-2 border-blue-200 space-y-3">
                        <p className="text-xs text-blue-600 font-semibold">📋 Upřesněte prosím:</p>
                        {q.followup.fields.map((field) => (
                          <div key={field.key}>
                            <label className="block text-sm text-gray-600 mb-1">{field.label}</label>
                            {field.type === "text" ? (
                              <input
                                type="text"
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="Vyplňte..."
                                value={ans.details[field.key] || ""}
                                onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                              />
                            ) : (
                              <select
                                className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                                value={ans.details[field.key] || ""}
                                onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                              >
                                <option value="">Vyberte...</option>
                                {field.options?.map((opt) => (
                                  <option key={opt} value={opt}>{opt}</option>
                                ))}
                              </select>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Navigace */}
            <div className="flex justify-between mt-8">
              <button
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
                className="px-6 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-30"
              >
                ← Zpět
              </button>

              {isLastStep ? (
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !companyId}
                  className="px-6 py-3 rounded-lg text-sm font-bold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition"
                >
                  {submitting ? "⏳ Odesílám..." : "📤 Odeslat dotazník"}
                </button>
              ) : (
                <button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  className="px-6 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Další →
                </button>
              )}
            </div>
          </div>
        )}

        {/* Přehled sekcí */}
        <div className="mt-6 flex justify-center gap-2">
          {sections.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setCurrentStep(i)}
              className={`w-8 h-8 rounded-full text-xs font-bold transition ${
                i === currentStep
                  ? "bg-blue-600 text-white"
                  : i < currentStep
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
