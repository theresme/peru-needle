import { usePoll } from "./hooks/usePoll";
import Header from "./components/Header";
import Needle from "./components/Needle";
import Sparkline from "./components/Sparkline";
import CandidateCards from "./components/CandidateCards";
import VoteGap from "./components/VoteGap";
import ViradaCard from "./components/ViradaCard";
import LastHour from "./components/LastHour";
import TallyBar from "./components/TallyBar";
import WhatsLeft from "./components/WhatsLeft";
import ExpectedFinal from "./components/ExpectedFinal";
import EventFeed from "./components/EventFeed";
import WatchList from "./components/WatchList";
import ReasonsToWin from "./components/ReasonsToWin";
import DepartmentTable from "./components/DepartmentTable";
import Footer from "./components/Footer";

export default function App() {
  const { state, error, loading, lastFetch, refresh } = usePoll();

  return (
    <div className="min-h-full">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
        <Header
          lastFetch={lastFetch}
          fonte={state?.fonte}
          pollSeconds={state?.pollSeconds}
          onRefresh={refresh}
          error={error && state ? error : null}
        />

        {loading && !state && <LoadingState />}
        {!loading && !state && <ErrorState error={error} onRetry={refresh} />}

        {state && <SamplingWarning state={state} />}

        {state && (
          <main className="mt-8 space-y-6">
            {/* HERO: agulha */}
            <section className="rounded-2xl bg-gradient-to-b from-panel to-ink border border-hair p-6 sm:p-8">
              <Needle modelo={state.modelo} />
              <Sparkline tick={state.timestamp} />
            </section>

            <CandidateCards candidatos={state.candidatos} ultimaHora={state.ultimaHora} />

            <VoteGap candidatos={state.candidatos} tick={state.timestamp} />

            <ViradaCard virada={state.virada} />

            <LastHour ultimaHora={state.ultimaHora} />

            <ExpectedFinal modelo={state.modelo} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TallyBar atas={state.atas} pctApurado={state.pctApurado} />
              <WhatsLeft
                atas={state.atas}
                domestico={state.domestico}
                exterior={state.exterior}
                modelo={state.modelo}
              />
            </div>

            <EventFeed eventos={state.eventos} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <WatchList rows={state.porDepartamento} exterior={state.exterior} />
              <ReasonsToWin
                candidatos={state.candidatos}
                rows={state.porDepartamento}
                exterior={state.exterior}
                modelo={state.modelo}
              />
            </div>

            <DepartmentTable rows={state.porDepartamento} />
          </main>
        )}

        <Footer />
      </div>
    </div>
  );
}

// Limiar de "corrida apertada": abaixo disso o resultado pode virar conforme
// as atas restantes (exterior + pendentes no JEE) entram.
const TIGHT_RACE_PP = 1.5;

function SamplingWarning({ state }) {
  if (state?.fonte !== "onpe") return null;
  const [a, b] = state.candidatos ?? [];
  if (!a || !b) return null;
  const margem = Math.abs(a.pctAtual - b.pctAtual);
  const restantes = state.atas?.restantes ?? 0;
  if (margem > TIGHT_RACE_PP) return null;

  const fmt = (n) =>
    n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs leading-relaxed text-amber-200/90">
      <span className="font-semibold">Corrida apertadíssima:</span> os números são
      oficiais da ONPE (votos válidos), mas a margem é de apenas{" "}
      <span className="num font-semibold">{fmt(margem)} pp</span>. Ainda faltam{" "}
      <span className="num font-semibold">{restantes.toLocaleString("pt-BR")}</span>{" "}
      atas (exterior + pendentes no JEE) — o resultado pode virar. A agulha reflete a
      probabilidade do modelo, não um vencedor definido.
    </div>
  );
}

function LoadingState() {
  return (
    <div className="mt-16 flex flex-col items-center text-gray-500">
      <div className="h-10 w-10 rounded-full border-2 border-hair border-t-gray-400 animate-spin" />
      <p className="mt-4 text-sm">Carregando primeira apuração…</p>
    </div>
  );
}

function ErrorState({ error, onRetry }) {
  return (
    <div className="mt-16 flex flex-col items-center text-center">
      <div className="text-4xl mb-3">⚠️</div>
      <p className="text-gray-300 font-semibold">Não foi possível carregar os dados</p>
      <p className="text-sm text-gray-500 mt-1 max-w-md">{error || "tente novamente"}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-lg border border-hair bg-panel px-4 py-2 text-sm text-gray-200 hover:bg-panel2"
      >
        Tentar de novo
      </button>
    </div>
  );
}
