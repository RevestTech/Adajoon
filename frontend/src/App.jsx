import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChannelGrid from "./components/ChannelGrid";
import RadioGrid from "./components/RadioGrid";
import VideoPlayer from "./components/VideoPlayer";
import RadioPlayer from "./components/RadioPlayer";
import FavoritesView from "./components/FavoritesView";
import useFavorites, { useRadioFavorites } from "./hooks/useFavorites";
import { useAuth } from "./hooks/useAuth";
import { useVotes } from "./hooks/useVotes";

const LandingPage = lazy(() => import("./components/LandingPage"));
import { fetchChannels, fetchCategories, fetchCountries, fetchStats } from "./api/channels";
import { fetchRadioStations, fetchRadioTags, fetchRadioCountries } from "./api/radio";

const GOOGLE_CLIENT_ID = "735750557405-01nak31482018qbfu1sigov94c1k4ca7.apps.googleusercontent.com";
const APPLE_CLIENT_ID = "com.adajoon.web";

export default function App() {
  const [mode, setMode] = useState("tv");
  const [viewMode, setViewMode] = useState(() => localStorage.getItem("adajoon_view") || "grid");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showLogin, setShowLogin] = useState(() => {
    try { return !localStorage.getItem("adajoon_user") && !localStorage.getItem("adajoon_guest_skip"); } catch { return true; }
  });

  const auth = useAuth();
  const isGuest = !auth.user;

  const handleViewToggle = (v) => {
    setViewMode(v);
    localStorage.setItem("adajoon_view", v);
  };

  // TV state
  const [channels, setChannels] = useState([]);
  const [categories, setCategories] = useState([]);
  const [countries, setCountries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [activeCategories, setActiveCategories] = useState([]);
  const [activeCountries, setActiveCountries] = useState([]);
  const [showFavorites, setShowFavorites] = useState(false);
  const [activeQualities, setActiveQualities] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [selectedChannel, setSelectedChannel] = useState(null);

  // Radio state
  const [radioStations, setRadioStations] = useState([]);
  const [radioTags, setRadioTags] = useState([]);
  const [radioCountries, setRadioCountries] = useState([]);
  const [radioLoading, setRadioLoading] = useState(true);
  const [radioError, setRadioError] = useState(null);
  const [radioSearch, setRadioSearch] = useState("");
  const [activeTags, setActiveTags] = useState([]);
  const [activeRadioCountries, setActiveRadioCountries] = useState([]);
  const [activeRadioQualities, setActiveRadioQualities] = useState([]);
  const [radioPage, setRadioPage] = useState(1);
  const [radioTotalPages, setRadioTotalPages] = useState(0);
  const [radioTotal, setRadioTotal] = useState(0);
  const [selectedStation, setSelectedStation] = useState(null);
  const [showRadioFavorites, setShowRadioFavorites] = useState(false);

  const { favorites, favoritesList, favoritesCount, toggleFavorite, isFavorite, loadFromServer } = useFavorites();
  const {
    favorites: radioFavorites,
    favoritesList: radioFavoritesList,
    favoritesCount: radioFavoritesCount,
    toggleFavorite: toggleRadioFavorite,
    isFavorite: isRadioFavorite,
    loadFromServer: loadRadioFromServer,
  } = useRadioFavorites();

  const votes = useVotes();

  useEffect(() => {
    if (auth.user) {
      votes.resetLoaded();
      votes.loadMyVotes("tv");
      votes.loadMyVotes("radio");
    }
  }, [auth.user]);

  useEffect(() => {
    if (channels.length) {
      votes.loadSummary("tv", channels.map((c) => c.id));
    }
  }, [channels]);

  useEffect(() => {
    if (radioStations.length) {
      votes.loadSummary("radio", radioStations.map((s) => s.id));
    }
  }, [radioStations]);

  const syncAfterLogin = useCallback(async () => {
    setShowLogin(false);
    const localTv = Object.values(favorites).map((ch) => ({
      item_type: "tv", item_id: ch.id, item_data: ch,
    }));
    const localRadio = Object.values(radioFavorites || {}).map((st) => ({
      item_type: "radio", item_id: st.id, item_data: st,
    }));
    const merged = await auth.syncFavorites([...localTv, ...localRadio]);
    if (merged) { loadFromServer(merged); loadRadioFromServer(merged); }
  }, [auth, favorites, radioFavorites, loadFromServer, loadRadioFromServer]);

  const handleGoogleLogin = useCallback(async (credential) => {
    const user = await auth.loginWithGoogle(credential);
    if (user) await syncAfterLogin();
  }, [auth, syncAfterLogin]);

  const handleAppleLogin = useCallback(async (idToken, userName) => {
    const user = await auth.loginWithApple(idToken, userName);
    if (user) await syncAfterLogin();
  }, [auth, syncAfterLogin]);

  const handlePasskeyLogin = useCallback(async () => {
    const user = await auth.loginWithPasskey();
    if (user) await syncAfterLogin();
  }, [auth, syncAfterLogin]);

  const handleLogout = useCallback(() => {
    auth.logout();
    localStorage.removeItem("adajoon_guest_skip");
    setShowLogin(true);
  }, [auth]);

  useEffect(() => {
    if (!auth.user) return;
    auth.fetchFavorites().then((serverFavs) => {
      if (serverFavs) {
        loadFromServer(serverFavs);
        loadRadioFromServer(serverFavs);
      }
    });
  }, [auth.user]);

  // TV: load metadata
  const loadMeta = useCallback(async () => {
    try {
      const [cats, ctrs, st] = await Promise.all([
        fetchCategories(), fetchCountries(), fetchStats(),
      ]);
      setCategories(cats);
      setCountries(ctrs);
      setStats(st);
    } catch { /* retry later */ }
  }, []);

  // TV: load channels
  const loadChannels = useCallback(async () => {
    if (showFavorites) return;
    if (channels.length === 0) setLoading(true);
    setError(null);
    try {
      const data = await fetchChannels({
        query: search || undefined,
        category: activeCategories.length ? activeCategories.join(",") : undefined,
        country: activeCountries.length ? activeCountries.join(",") : undefined,
        status: activeQualities.length ? activeQualities.join(",") : undefined,
        page,
      });
      setChannels(data.channels);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch {
      setError("Unable to load channels. The server may still be syncing data.");
    } finally {
      setLoading(false);
    }
  }, [search, activeCategories, activeCountries, activeQualities, page, showFavorites]);

  // Radio: load metadata
  const loadRadioMeta = useCallback(async () => {
    try {
      const [tags, ctrs] = await Promise.all([
        fetchRadioTags(), fetchRadioCountries(),
      ]);
      setRadioTags(tags);
      setRadioCountries(ctrs);
    } catch { /* retry later */ }
  }, []);

  // Radio: load stations
  const loadRadio = useCallback(async () => {
    if (showRadioFavorites) return;
    if (radioStations.length === 0) setRadioLoading(true);
    setRadioError(null);
    try {
      const data = await fetchRadioStations({
        query: radioSearch || undefined,
        tag: activeTags.length ? activeTags.join(",") : undefined,
        country: activeRadioCountries.length ? activeRadioCountries.join(",") : undefined,
        status: activeRadioQualities.length ? activeRadioQualities.join(",") : undefined,
        page: radioPage,
      });
      setRadioStations(data.stations);
      setRadioTotalPages(data.total_pages);
      setRadioTotal(data.total);
    } catch {
      setRadioError("Unable to load radio stations. Data may still be syncing.");
    } finally {
      setRadioLoading(false);
    }
  }, [radioSearch, activeTags, activeRadioCountries, activeRadioQualities, radioPage, showRadioFavorites]);

  useEffect(() => {
    loadMeta();
    const interval = setInterval(loadMeta, 30000);
    return () => clearInterval(interval);
  }, [loadMeta]);

  useEffect(() => { loadChannels(); }, [loadChannels]);
  useEffect(() => { setPage(1); }, [search, activeCategories, activeCountries, showFavorites, activeQualities]);

  useEffect(() => {
    if (mode === "radio") loadRadioMeta();
  }, [mode, loadRadioMeta]);

  useEffect(() => {
    if (mode === "radio") loadRadio();
  }, [mode, loadRadio]);

  useEffect(() => { setRadioPage(1); }, [radioSearch, activeTags, activeRadioCountries, activeRadioQualities, showRadioFavorites]);

  const displayedChannels = showFavorites ? favoritesList : channels;
  const displayedTotal = showFavorites ? favoritesCount : total;
  const displayedTotalPages = showFavorites ? 1 : totalPages;

  const displayedRadioStations = showRadioFavorites ? radioFavoritesList : radioStations;
  const displayedRadioTotal = showRadioFavorites ? radioFavoritesCount : radioTotal;
  const displayedRadioTotalPages = showRadioFavorites ? 1 : radioTotalPages;

  const clearFilter = (type, value) => {
    if (type === "category") {
      if (value) setActiveCategories((prev) => prev.filter((c) => c !== value));
      else setActiveCategories([]);
    }
    if (type === "country") {
      if (mode === "tv") {
        if (value) setActiveCountries((prev) => prev.filter((c) => c !== value));
        else setActiveCountries([]);
      } else {
        if (value) setActiveRadioCountries((prev) => prev.filter((c) => c !== value));
        else setActiveRadioCountries([]);
      }
    }
    if (type === "tag") {
      if (value) setActiveTags((prev) => prev.filter((t) => t !== value));
      else setActiveTags([]);
    }
    if (type === "search") { if (mode === "tv") setSearch(""); else setRadioSearch(""); }
    if (type === "favorites") { setShowFavorites(false); setShowRadioFavorites(false); }
    if (type === "quality") {
      if (value) {
        if (mode === "tv") setActiveQualities((prev) => prev.filter((q) => q !== value));
        else setActiveRadioQualities((prev) => prev.filter((q) => q !== value));
      } else {
        setActiveQualities([]);
        setActiveRadioQualities([]);
      }
    }
  };

  const handleToggleFavorites = () => {
    const turning_on = !showFavorites;
    setShowFavorites(turning_on);
    setShowRadioFavorites(turning_on);
    if (turning_on) {
      setActiveCategories([]); setActiveCountries([]); setSearch(""); setActiveQualities([]);
      setActiveTags([]); setActiveRadioCountries([]); setRadioSearch(""); setActiveRadioQualities([]);
    }
  };

  const handleTvQualityChange = useCallback((key) => {
    if (key === "all") { setActiveQualities([]); return; }
    const val = key === "hide_dead" ? "hide_offline" : key;
    setActiveQualities((prev) => prev.includes(val) ? prev.filter((q) => q !== val) : [...prev, val]);
  }, []);

  const handleRadioQualityChange = useCallback((key) => {
    if (key === "all") { setActiveRadioQualities([]); return; }
    const val = key === "hide_dead" ? "hide_offline" : key;
    setActiveRadioQualities((prev) => prev.includes(val) ? prev.filter((q) => q !== val) : [...prev, val]);
  }, []);

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
    setSelectedChannel(null);
    setSelectedStation(null);
  };

  return (
    <>
      <Header
        mode={mode}
        onModeSwitch={handleModeSwitch}
        search={mode === "tv" ? search : radioSearch}
        onSearch={(val) => {
          if (mode === "tv") { setSearch(val); setShowFavorites(false); }
          else { setRadioSearch(val); setShowRadioFavorites(false); }
        }}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        user={auth.user}
        onLogin={() => setShowLogin(true)}
        onLogout={handleLogout}
        showFavorites={showFavorites}
        onToggleFavorites={handleToggleFavorites}
        favoritesCount={favoritesCount + radioFavoritesCount}
        isGuest={isGuest}
      />
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <div className="layout">
        <Sidebar
          className={sidebarOpen ? "open" : ""}
          mode={mode}
          categories={categories}
          countries={mode === "tv" ? countries : []}
          activeCategories={activeCategories}
          activeCountries={mode === "tv" ? activeCountries : activeRadioCountries}
          onSelectCategory={(id) => {
            if (!id) { setActiveCategories([]); }
            else { setActiveCategories((prev) => prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]); }
            setShowFavorites(false);
          }}
          onSelectCountry={(code) => {
            if (!code) {
              if (mode === "tv") setActiveCountries([]);
              else setActiveRadioCountries([]);
            } else if (mode === "tv") {
              setActiveCountries((prev) => prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]);
              setShowFavorites(false);
            } else {
              setActiveRadioCountries((prev) => prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]);
              setShowRadioFavorites(false);
            }
          }}
          favoritesCount={favoritesCount + radioFavoritesCount}
          showFavorites={showFavorites}
          onToggleFavorites={handleToggleFavorites}
          radioTags={radioTags}
          radioCountries={radioCountries}
          activeTags={activeTags}
          onSelectTag={(t) => {
            if (!t) { setActiveTags([]); }
            else { setActiveTags((prev) => prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]); }
            setShowRadioFavorites(false);
          }}
          isGuest={isGuest}
          onLogin={() => setShowLogin(true)}
        />
        <main className="main-content">
          {showFavorites ? (
            <FavoritesView
              tvFavorites={favoritesList}
              radioFavorites={radioFavoritesList}
              onSelectChannel={setSelectedChannel}
              onSelectStation={setSelectedStation}
              isTvFavorite={isFavorite}
              isRadioFavorite={isRadioFavorite}
              onToggleTvFavorite={toggleFavorite}
              onToggleRadioFavorite={toggleRadioFavorite}
              onClearFavorites={() => { setShowFavorites(false); setShowRadioFavorites(false); }}
            />
          ) : mode === "tv" ? (
            <ChannelGrid
              channels={channels}
              loading={loading}
              error={error}
              total={total}
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
              onSelect={setSelectedChannel}
              activeCategories={activeCategories}
              activeCountries={activeCountries}
              categoryList={categories}
              search={search}
              showFavorites={false}
              activeQualities={activeQualities}
              onQualityChange={handleTvQualityChange}
              onClearFilter={clearFilter}
              onRetry={loadChannels}
              isFavorite={isFavorite}
              onToggleFavorite={toggleFavorite}
              viewMode={viewMode}
              onViewToggle={handleViewToggle}
              isGuest={isGuest}
              onLogin={() => setShowLogin(true)}
              getVoteSummary={(id) => votes.getSummaryFor("tv", id)}
              stats={stats}
            />
          ) : (
            <RadioGrid
              stations={radioStations}
              loading={radioLoading}
              error={radioError}
              total={radioTotal}
              page={radioPage}
              totalPages={radioTotalPages}
              onPageChange={setRadioPage}
              onSelect={setSelectedStation}
              activeTags={activeTags}
              activeCountries={activeRadioCountries}
              search={radioSearch}
              showFavorites={false}
              activeQualities={activeRadioQualities}
              onQualityChange={handleRadioQualityChange}
              onClearFilter={clearFilter}
              onRetry={loadRadio}
              isFavorite={isRadioFavorite}
              onToggleFavorite={toggleRadioFavorite}
              viewMode={viewMode}
              onViewToggle={handleViewToggle}
              isGuest={isGuest}
              onLogin={() => setShowLogin(true)}
              getVoteSummary={(id) => votes.getSummaryFor("radio", id)}
              stats={stats}
            />
          )}
        </main>
      </div>
      {selectedChannel && (
        <VideoPlayer
          channel={selectedChannel}
          onClose={() => setSelectedChannel(null)}
          isFavorite={isFavorite(selectedChannel.id)}
          onToggleFavorite={() => toggleFavorite(selectedChannel)}
          isGuest={isGuest}
          onLogin={() => setShowLogin(true)}
          myVotes={votes.getMyVotesFor("tv", selectedChannel.id)}
          voteSummary={votes.getSummaryFor("tv", selectedChannel.id)}
          onVote={votes.submitVote}
        />
      )}
      {selectedStation && (
        <RadioPlayer
          station={selectedStation}
          onClose={() => setSelectedStation(null)}
          isFavorite={isRadioFavorite(selectedStation.id)}
          onToggleFavorite={() => toggleRadioFavorite(selectedStation)}
          isGuest={isGuest}
          onLogin={() => setShowLogin(true)}
          myVotes={votes.getMyVotesFor("radio", selectedStation.id)}
          voteSummary={votes.getSummaryFor("radio", selectedStation.id)}
          onVote={votes.submitVote}
        />
      )}
      {showLogin && !auth.user && (
        <Suspense fallback={null}>
          <LandingPage
            onGoogleLogin={handleGoogleLogin}
            onAppleLogin={handleAppleLogin}
            onPasskeyLogin={handlePasskeyLogin}
            googleClientId={GOOGLE_CLIENT_ID}
            appleClientId={APPLE_CLIENT_ID}
            onSkip={() => { localStorage.setItem("adajoon_guest_skip", "1"); setShowLogin(false); }}
          />
        </Suspense>
      )}
      <footer className="app-footer">
        <span>&copy; {new Date().getFullYear()} Revest Technology. All rights reserved.</span>
        <span className="footer-version">v2.0.0</span>
      </footer>
    </>
  );
}
