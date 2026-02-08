export default function PricingPage() {
    const plans = [
        {
            name: "BASIC",
            price: "4 999",
            description: "Compliance Kit — dokumenty ke stažení",
            features: [
                "Sken webu + report",
                "AI Act Compliance Kit (PDF)",
                "Transparenční stránka",
                "Akční plán s checkboxy",
                "JavaScript widget kód",
                "Jednorázová dodávka",
            ],
            cta: "Objednat BASIC",
            highlighted: false,
        },
        {
            name: "PRO",
            price: "14 999",
            description: "Vše z BASIC + implementace na klíč",
            features: [
                "Vše z BASIC",
                "Instalace widgetu na váš web",
                "Nastavení transparenční stránky",
                "Úprava chatbot oznámení",
                "Podpora po dobu 30 dní",
                "Funguje na WordPress, Shoptet i custom",
            ],
            cta: "Objednat PRO",
            highlighted: true,
        },
        {
            name: "ENTERPRISE",
            price: "49 999+",
            description: "Kompletní řešení + právní review + monitoring",
            features: [
                "Vše z PRO",
                "Konzultace s AI Act specialistou",
                "Právní review dokumentů",
                "Měsíční monitoring (299 Kč/měs)",
                "Dotazník interních AI systémů",
                "Školení AI literacy (čl. 4)",
            ],
            cta: "Kontaktovat nás",
            highlighted: false,
        },
    ];

    return (
        <section className="py-20">
            <div className="mx-auto max-w-7xl px-6">
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-gray-900">Ceník</h1>
                    <p className="mt-4 text-gray-500">
                        Vyberte si balíček podle velikosti vaší firmy a potřeb.
                    </p>
                </div>

                <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
                    {plans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`card flex flex-col ${plan.highlighted
                                    ? "ring-2 ring-shield-600 shadow-lg scale-105"
                                    : ""
                                }`}
                        >
                            {plan.highlighted && (
                                <div className="mb-4 inline-flex self-start rounded-full bg-shield-100 px-3 py-1 text-xs font-semibold text-shield-700">
                                    ⭐ Nejoblíbenější
                                </div>
                            )}
                            <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                            <div className="mt-2">
                                <span className="text-4xl font-extrabold text-shield-600">
                                    {plan.price}
                                </span>
                                <span className="text-gray-500"> Kč</span>
                            </div>
                            <p className="mt-2 text-sm text-gray-500">{plan.description}</p>

                            <ul className="mt-6 flex-1 space-y-3">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-2 text-sm text-gray-600">
                                        <span className="text-success-500 mt-0.5">✓</span>
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            <div className="mt-8">
                                <a
                                    href={plan.name === "ENTERPRISE" ? "/contact" : "/scan"}
                                    className={`w-full ${plan.highlighted ? "btn-primary" : "btn-secondary"} block text-center`}
                                >
                                    {plan.cta}
                                </a>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Monitoring addon */}
                <div className="mt-12 text-center">
                    <div className="card inline-block">
                        <p className="text-sm text-gray-500">
                            🔄 <strong>Měsíční monitoring:</strong> 299 Kč/měsíc —
                            automatický resken, alerty při změnách, aktualizace widgetu.
                            Dostupný ke všem balíčkům.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}
