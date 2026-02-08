export default function ScanPage() {
    return (
        <section className="py-20">
            <div className="mx-auto max-w-3xl px-6 text-center">
                <h1 className="text-3xl font-bold text-gray-900">🔍 Skenovat web</h1>
                <p className="mt-4 text-gray-500">
                    Zadejte URL vašeho webu a zjistěte, jaké AI systémy na něm běží.
                </p>

                <form className="mt-8 flex gap-3 max-w-xl mx-auto">
                    <input
                        type="url"
                        name="url"
                        placeholder="https://vasefirma.cz"
                        className="flex-1 rounded-lg border border-gray-300 px-4 py-3
                       focus:ring-2 focus:ring-shield-500 focus:border-shield-500"
                        required
                    />
                    <button type="submit" className="btn-primary whitespace-nowrap">
                        Skenovat
                    </button>
                </form>

                {/* Výsledky se zobrazí zde — implementace v Fázi B */}
                <div className="mt-12 card text-left">
                    <p className="text-sm text-gray-400 text-center">
                        ⏳ Výsledky skenu se zobrazí zde po implementaci scanneru (Fáze B).
                    </p>
                </div>
            </div>
        </section>
    );
}
