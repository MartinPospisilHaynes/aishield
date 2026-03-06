import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-dark-900 text-slate-100">
      <div className="max-w-lg w-full text-center">
        {/* Neon 404 */}
        <div className="relative mb-8">
          <span className="text-[120px] md:text-[160px] font-black leading-none bg-gradient-to-r from-fuchsia-500 via-purple-500 to-cyan-400 bg-clip-text text-transparent select-none">
            404
          </span>
          <div className="absolute inset-0 blur-3xl opacity-20 bg-gradient-to-r from-fuchsia-500 via-purple-500 to-cyan-400 rounded-full" />
        </div>

        {/* Glass card */}
        <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
          <h1 className="text-2xl font-bold text-white mb-3">
            Stránka nenalezena
          </h1>
          <p className="text-slate-400 mb-8 leading-relaxed">
            Omlouváme se, ale tato stránka neexistuje nebo byla přesunuta.
            Zkontrolujte prosím adresu nebo se vraťte na domovskou stránku.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-fuchsia-600 hover:bg-fuchsia-500 text-white font-medium transition-colors"
            >
              <span>🏠</span>
              Zpět na hlavní stránku
            </Link>
            <Link
              href="/scan"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-white/10 hover:border-fuchsia-500/50 hover:bg-white/[0.04] text-slate-300 font-medium transition-all"
            >
              <span>🔍</span>
              Skenovat web zdarma
            </Link>
          </div>
        </div>

        {/* Kontakt */}
        <p className="mt-8 text-sm text-slate-500">
          Potřebujete pomoc?{" "}
          <a
            href="mailto:info@aishield.cz"
            className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors"
          >
            info@aishield.cz
          </a>
          {" · "}
          <a
            href="tel:+420732716141"
            className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors"
          >
            +420 732 716 141
          </a>
        </p>
      </div>
    </div>
  );
}
