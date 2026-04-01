import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChannelGrid from "./components/ChannelGrid";
import RadioGrid from "./components/RadioGrid";
import VideoPlayer from "./components/VideoPlayer";
import RadioPlayer from "./components/RadioPlayer";
import LoginModal from "./components/LoginModal";
import FavoritesView from "./components/FavoritesView";
import useFavorites, { useRadioFavorites } from "./hooks/useFavorites";
import { useAuth } from "./hooks/useAuth";
import { fetchChannels, fetchCategories, fetchCountries, fetchStats } from "./api/channels";
import { fetchRadioStations, fetchRadioTags, fetchRadioCountries } from "./api/radio";

const GOOGLE_CLIENT_ID = "735750557405-01nak31482018qbfu1sigov94c1k4ca7.apps.googleusercontent.com";

export default function App() {
  const [mode, setMode] = useState("tv");
  const [viewMode, setViewMode] = useState(() => localStorage.getItem("adajoon_view") || "grid");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  const auth = useAuth();

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
  const [activeCategory, setActiveCategory] = useState(null);
  const [activeCountry, setActiveCountry] = useState(null);
  const [showFavorites, setShowFavorites] = useState(false);
  const [liveOnly, setLiveOnly] = useState(false);
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
  const [activeTag, setActiveTag] = useState(null);
  const [activeRadioCountry, setActiveRadioCountry] = useState(null);
  const [workingOnly, setWorkingOnly] = useState(false);
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

  const handleGoogleLogin = useCallback(async (credential) => {
    const user = await auth.loginWithGoogle(credential);
    if (!user) return;
    setShowLogin(false);

    const localTv = Object.values(favorites).map((ch) => ({
      item_type: "tv",
      item_id: ch.id,
      item_data: ch,
    }));
    const localRadio = Object.values(radioFavorites || {}).map((st) => ({
      item_type: "radio",
      item_id: st.id,
      item_data: st,
    }));
    const merged = await auth.syncFavorites([...localTv, ...localRadio]);
    if (merged) {
      loadFromServer(merged);
      loadRadioFromServer(merged);
    }
  }, [auth, favorites, radioFavorites, loadFromServer, loadRadioFromServer]);

  const handleLogout = useCallback(() => {
    auth.logout();
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
    setLoading(true);
    setError(null);
    try {
      const data = await fetchChannels({
        query: search || undefined,
        category: activeCategory || undefined,
        country: activeCountry || undefined,
        liveOnly: liveOnly || undefined,
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
  }, [search, activeCategory, activeCountry, liveOnly, page, showFavorites]);

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
    setRadioLoading(true);
    setRadioError(null);
    try {
      const data = await fetchRadioStations({
        query: radioSearch || undefined,
        tag: activeTag || undefined,
        country: activeRadioCountry || undefined,
        workingOnly: workingOnly || undefined,
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
  }, [radioSearch, activeTag, activeRadioCountry, workingOnly, radioPage, showRadioFavorites]);

  useEffect(() => {
    loadMeta();
    const interval = setInterval(loadMeta, 30000);
    return () => clearInterval(interval);
  }, [loadMeta]);

  useEffect(() => { loadChannels(); }, [loadChannels]);
  useEffect(() => { setPage(1); }, [search, activeCategory, activeCountry, showFavorites, liveOnly]);

  useEffect(() => {
    if (mode === "radio") { loadRadioMeta(); loadRadio(); }
  }, [mode, loadRadioMeta, loadRadio]);

  useEffect(() => { setRadioPage(1); }, [radioSearch, activeTag, activeRadioCountry, workingOnly, showRadioFavorites]);

  const displayedChannels = showFavorites ? favoritesList : channels;
  const displayedTotal = showFavorites ? favoritesCount : total;
  const displayedTotalPages = showFavorites ? 1 : totalPages;

  const displayedRadioStations = showRadioFavorites ? radioFavoritesList : radioStations;
  const displayedRadioTotal = showRadioFavorites ? radioFavoritesCount : radioTotal;
  const displayedRadioTotalPages = showRadioFavorites ? 1 : radioTotalPages;

  const clearFilter = (type) => {
    if (type === "category") setActiveCategory(null);
    if (type === "country") { if (mode === "tv") setActiveCountry(null); else setActiveRadioCountry(null); }
    if (type === "search") { if (mode === "tv") setSearch(""); else setRadioSearch(""); }
    if (type === "favorites") { setShowFavorites(false); setShowRadioFavorites(false); }
    if (type === "liveOnly") setLiveOnly(false);
    if (type === "tag") setActiveTag(null);
    if (type === "workingOnly") setWorkingOnly(false);
  };

  const handleToggleFavorites = () => {
    const turning_on = !showFavorites;
    setShowFavorites(turning_on);
    setShowRadioFavorites(turning_on);
    if (turning_on) {
      setActiveCategory(null); setActiveCountry(null); setSearch("");
      setActiveTag(null); setActiveRadioCountry(null); setRadioSearch("");
    }
  };

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
          else setRadioSearch(val);
        }}
        stats={stats}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        user={auth.user}
        onLogin={() => setShowLogin(true)}
        onLogout={handleLogout}
      />
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <div className="layout">
        <Sidebar
          className={sidebarOpen ? "open" : ""}
          mode={mode}
          categories={categories}
          countries={mode === "tv" ? countries : []}
          activeCategory={activeCategory}
          activeCountry={mode === "tv" ? activeCountry : activeRadioCountry}
          onSelectCategory={(id) => { setActiveCategory(id === activeCategory ? null : id); setShowFavorites(false); }}
          onSelectCountry={(code) => {
            if (mode === "tv") { setActiveCountry(code === activeCountry ? null : code); setShowFavorites(false); }
            else { setActiveRadioCountry(code === activeRadioCountry ? null : code); setShowRadioFavorites(false); }
          }}
          favoritesCount={favoritesCount + radioFavoritesCount}
          showFavorites={showFavorites}
          onToggleFavorites={handleToggleFavorites}
          radioTags={radioTags}
          radioCountries={radioCountries}
          activeTag={activeTag}
          onSelectTag={(t) => { setActiveTag(t === activeTag ? null : t); setShowRadioFavorites(false); }}
          liveOnly={mode === "tv" ? liveOnly : workingOnly}
          onToggleLiveOnly={() => {
            if (mode === "tv") setLiveOnly((v) => !v);
            else setWorkingOnly((v) => !v);
          }}
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
              activeCategory={activeCategory}
              activeCountry={activeCountry}
              search={search}
              showFavorites={false}
              liveOnly={liveOnly}
              onClearFilter={clearFilter}
              onRetry={loadChannels}
              isFavorite={isFavorite}
              onToggleFavorite={toggleFavorite}
              viewMode={viewMode}
              onViewToggle={handleViewToggle}
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
              activeTag={activeTag}
              activeCountry={activeRadioCountry}
              search={radioSearch}
              showFavorites={false}
              workingOnly={workingOnly}
              onClearFilter={clearFilter}
              onRetry={loadRadio}
              isFavorite={isRadioFavorite}
              onToggleFavorite={toggleRadioFavorite}
              viewMode={viewMode}
              onViewToggle={handleViewToggle}
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
        />
      )}
      {selectedStation && (
        <RadioPlayer
          station={selectedStation}
          onClose={() => setSelectedStation(null)}
          isFavorite={isRadioFavorite(selectedStation.id)}
          onToggleFavorite={() => toggleRadioFavorite(selectedStation)}
        />
      )}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onGoogleLogin={handleGoogleLogin}
          googleClientId={GOOGLE_CLIENT_ID}
        />
      )}
    </>
  );
}
