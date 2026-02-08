export default function LoginPage() {
    return (
        <section className="py-20">
            <div className="mx-auto max-w-md px-6">
                <div className="text-center mb-8">
                    <span className="text-4xl">🛡️</span>
                    <h1 className="mt-4 text-2xl font-bold text-gray-900">Přihlášení</h1>
                    <p className="mt-2 text-sm text-gray-500">
                        Přihlaste se do svého AIshield účtu.
                    </p>
                </div>

                {/* Placeholder — implementace v Fázi G (úkol 24) */}
                <div className="card">
                    <form className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                            <input
                                type="email"
                                placeholder="vas@email.cz"
                                className="w-full rounded-lg border border-gray-300 px-4 py-3
                           focus:ring-2 focus:ring-shield-500 focus:border-shield-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Heslo</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                className="w-full rounded-lg border border-gray-300 px-4 py-3
                           focus:ring-2 focus:ring-shield-500 focus:border-shield-500"
                            />
                        </div>
                        <button type="button" className="btn-primary w-full" disabled>
                            Přihlásit se (brzy)
                        </button>
                    </form>
                    <p className="mt-4 text-center text-sm text-gray-400">
                        ⏳ Autentizace bude implementována v Fázi G (úkol 24).
                    </p>
                </div>
            </div>
        </section>
    );
}
