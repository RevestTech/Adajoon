import { useState, useEffect, useCallback, lazy, Suspense, useRef } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChannelGrid from "./components/ChannelGrid";
import RadioGrid from "./components/RadioGrid";
import VideoPlayer from "./components/VideoPlayer";
import RadioPlayer from "./components/RadioPlayer";
import MiniPlayer from "./components/MiniPlayer";
import GuestNoticeToast from "./components/GuestNoticeToast";
import FavoritesView from "./components/FavoritesView";
import RecentlyPlayed from "./components/RecentlyPlayed";
import useFavorites, { useRadioFavorites } from "./hooks/useFavorites";
import useRecentlyPlayed from "./hooks/useRecentlyPlayed";
import { useAuth } from "./hooks/useAuth";
import { useVotes } from "./hooks/useVotes";
import {
  readUrlParams,
  writeUrlParams,
  pushPlayerState,
  popPlayerState,
} from "./hooks/useUrlState";

const LandingPage = lazy(() => import("./components/LandingPage"));
import { fetchChannels, fetchCategories, fetchCountries, fetchStats } from "./api/channels";
import { fetchRadioStations, fetchRadioTags, fetchRadioCountries } from "./api/radio";

const GOOGLE_CLIENT_ID = "735750557405-01nak31482018qbfu1sigov94c1k4ca7.apps.googleusercontent.com";
const APPLE_CLIENT_ID = "com.adajoon.web";

function readInitialFromUrl() {
  const u = readUrlParams();
  let storedView = null;
  try {
    storedView = localStorage.getItem("adajoon_view");
  } catch {
    /* ignore */
  }
  const view = u.view || storedView || "grid";
  const viewMode = ["grid", "list", "thumb"].includes(view) ? view : "grid";
  return {
    mode: u.mode,
    viewMode,
    search: u.mode === "tv" ? u.q : "",
    radioSearch: u.mode === "radio" ? u.q : "",
    activeCategories: u.cat,
    activeTags: u.tag,
    activeCountries: u.mode === "tv" ? u.country : [],
    activeRadioCountries: u.mode === "radio" ? u.country : [],
    activeQualities: u.mode === "tv" ? u.status : [],
    activeRadioQualities: u.mode === "radio" ? u.status : [],
    page: u.mode === "tv" ? u.page : 1,
    radioPage: u.mode === "radio" ? u.page : 1,
    showFavorites: u.fav,
    showRadioFavorites: u.fav,
  };
}

const IU = readInitialFromUrl();

export default function App() {
  const [mode, setMode] = useState(IU.mode);
  const [viewMode, setViewMode] = useState(IU.viewMode);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarRailCollapsed, setSidebarRailCollapsed] = useState(() => {
    try {
      return localStorage.getItem("retv-sidebar-rail-collapsed") === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("retv-sidebar-rail-collapsed", sidebarRailCollapsed ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [sidebarRailCollapsed]);

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
  const [search, setSearch] = useState(IU.search);
  const [activeCategories, setActiveCategories] = useState(IU.activeCategories);
  const [activeCountries, setActiveCountries] = useState(IU.activeCountries);
  const [showFavorites, setShowFavorites] = useState(IU.showFavorites);
  const [activeQualities, setActiveQualities] = useState(IU.activeQualities);
  const [page, setPage] = useState(IU.page);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [selectedChannel, setSelectedChannel] = useState(null);

  // Radio state
  const [radioStations, setRadioStations] = useState([]);
  const [radioTags, setRadioTags] = useState([]);
  const [radioCountries, setRadioCountries] = useState([]);
  const [radioLoading, setRadioLoading] = useState(true);
  const [radioError, setRadioError] = useState(null);
  const [radioSearch, setRadioSearch] = useState(IU.radioSearch);
  const [activeTags, setActiveTags] = useState(IU.activeTags);
  const [activeRadioCountries, setActiveRadioCountries] = useState(IU.activeRadioCountries);
  const [activeRadioQualities, setActiveRadioQualities] = useState(IU.activeRadioQualities);
  const [radioPage, setRadioPage] = useState(IU.radioPage);
  const [radioTotalPages, setRadioTotalPages] = useState(0);
  const [radioTotal, setRadioTotal] = useState(0);
  const [selectedStation, setSelectedStation] = useState(null);
  const [radioModalOpen, setRadioModalOpen] = useState(true);
  const [tvModalOpen, setTvModalOpen] = useState(true);
  const radioAudioRef = useRef(null);
  const [showRadioFavorites, setShowRadioFavorites] = useState(IU.showRadioFavorites);

  const nowPlaying =
    selectedStation == null
      ? null
      : { type: "radio", station: selectedStation, modalOpen: radioModalOpen };

  const showDockedPlayer =
    (nowPlaying && !nowPlaying.modalOpen) ||
    Boolean(selectedChannel && !tvModalOpen);

  const [debouncedTvSearch, setDebouncedTvSearch] = useState(IU.search);
  const [debouncedRadioSearch, setDebouncedRadioSearch] = useState(IU.radioSearch);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedTvSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedRadioSearch(radioSearch), 300);
    return () => clearTimeout(t);
  }, [radioSearch]);

  useEffect(() => {
    writeUrlParams({
      mode,
      q: mode === "tv" ? debouncedTvSearch : debouncedRadioSearch,
      cat: activeCategories,
      country: mode === "tv" ? activeCountries : activeRadioCountries,
      tag: activeTags,
      status: mode === "tv" ? activeQualities : activeRadioQualities,
      page: mode === "tv" ? page : radioPage,
      view: viewMode,
      fav: showFavorites,
    });
  }, [
    mode,
    debouncedTvSearch,
    debouncedRadioSearch,
    activeCategories,
    activeCountries,
    activeTags,
    activeRadioCountries,
    activeQualities,
    activeRadioQualities,
    page,
    radioPage,
    viewMode,
    showFavorites,
  ]);

  useEffect(() => {
    const onPop = () => {
      setSelectedChannel(null);
      setSelectedStation(null);
      setRadioModalOpen(true);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const prevTvFiltersKey = useRef(null);
  const prevRadioFiltersKey = useRef(null);

  const { favorites, favoritesList, favoritesCount, toggleFavorite, isFavorite, loadFromServer } = useFavorites();
  const { addRecent, recentItems } = useRecentlyPlayed();
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
    if (selectedChannel) {
      setTvModalOpen(true);
      addRecent("tv", selectedChannel);
    }
  }, [selectedChannel, addRecent]);

  useEffect(() => {
    if (selectedStation) addRecent("radio", selectedStation);
  }, [selectedStation, addRecent]);

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

  useEffect(() => {
    const key = JSON.stringify({
      search,
      activeCategories,
      activeCountries,
      showFavorites,
      activeQualities,
    });
    if (prevTvFiltersKey.current === null) {
      prevTvFiltersKey.current = key;
      return;
    }
    if (prevTvFiltersKey.current !== key) {
      prevTvFiltersKey.current = key;
      setPage(1);
    }
  }, [search, activeCategories, activeCountries, showFavorites, activeQualities]);

  useEffect(() => {
    if (mode === "radio") loadRadioMeta();
  }, [mode, loadRadioMeta]);

  useEffect(() => {
    if (mode === "radio") loadRadio();
  }, [mode, loadRadio]);

  useEffect(() => {
    const key = JSON.stringify({
      radioSearch,
      activeTags,
      activeRadioCountries,
      activeRadioQualities,
      showRadioFavorites,
    });
    if (prevRadioFiltersKey.current === null) {
      prevRadioFiltersKey.current = key;
      return;
    }
    if (prevRadioFiltersKey.current !== key) {
      prevRadioFiltersKey.current = key;
      setRadioPage(1);
    }
  }, [radioSearch, activeTags, activeRadioCountries, activeRadioQualities, showRadioFavorites]);

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

  const openTvPlayer = useCallback((ch) => {
    if (!ch) return;
    pushPlayerState("tv", ch.id);
    setSelectedStation(null);
    setSelectedChannel(ch);
  }, []);

  const closeTvPlayer = useCallback(() => {
    setSelectedChannel(null);
    popPlayerState();
  }, []);

  const stopRadio = useCallback(() => {
    const a = radioAudioRef.current;
    if (a) {
      a.pause();
      a.removeAttribute("src");
      a.load();
    }
    setSelectedStation(null);
    setRadioModalOpen(true);
    popPlayerState();
  }, []);

  const handleSelectStation = useCallback((station) => {
    if (!station) return;
    pushPlayerState("radio", station.id);
    setSelectedChannel(null);
    setSelectedStation(station);
    setRadioModalOpen(true);
  }, []);

  const handleModeSwitch = (newMode) => {
    if (selectedChannel || selectedStation) {
      setSelectedChannel(null);
      setSelectedStation(null);
      setRadioModalOpen(true);
      popPlayerState();
    }
    setMode(newMode);
  };

  const handleRecentSelect = useCallback(
    (item) => {
      if (item.type === "tv") {
        const ch =
          channels.find((c) => c.id === item.id) ||
          favorites[item.id] ||
          { id: item.id, name: item.name, logo: item.logo };
        openTvPlayer(ch);
      } else {
        const st =
          radioStations.find((s) => s.id === item.id) ||
          radioFavorites[item.id] ||
          { id: item.id, name: item.name, favicon: item.logo };
        handleSelectStation(st);
      }
    },
    [channels, radioStations, favorites, radioFavorites, openTvPlayer, handleSelectStation]
  );

  const searching = mode === "tv" ? Boolean(search.trim()) : Boolean(radioSearch.trim());
  const showRecentRow = !showFavorites && !searching;

  const [guestNotice, setGuestNotice] = useState(null);
  const guestNoticeTimerRef = useRef(null);
  const onGuestNotice = useCallback((msg) => {
    setGuestNotice(msg);
    if (guestNoticeTimerRef.current) clearTimeout(guestNoticeTimerRef.current);
    guestNoticeTimerRef.current = setTimeout(() => setGuestNotice(null), 6500);
  }, []);
  const dismissGuestNotice = useCallback(() => {
    setGuestNotice(null);
    if (guestNoticeTimerRef.current) clearTimeout(guestNoticeTimerRef.current);
  }, []);
  const guestNoticeSignIn = useCallback(() => {
    dismissGuestNotice();
    setShowLogin(true);
  }, [dismissGuestNotice]);

  useEffect(() => () => {
    if (guestNoticeTimerRef.current) clearTimeout(guestNoticeTimerRef.current);
  }, []);

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
        sidebarRailCollapsed={sidebarRailCollapsed}
        onToggleSidebarRail={() => setSidebarRailCollapsed((v) => !v)}
        user={auth.user}
        onLogin={() => setShowLogin(true)}
        onLogout={handleLogout}
        showFavorites={showFavorites}
        onToggleFavorites={handleToggleFavorites}
        favoritesCount={favoritesCount + radioFavoritesCount}
        isGuest={isGuest}
        onGuestNotice={onGuestNotice}
      />
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <div className="layout">
        <Sidebar
          className={sidebarOpen ? "open" : ""}
          railCollapsed={sidebarRailCollapsed}
          onToggleRail={() => setSidebarRailCollapsed((v) => !v)}
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
          onGuestNotice={onGuestNotice}
        />
        <main className={`main-content${showDockedPlayer ? " main-content--mini-player" : ""}`}>
          {showRecentRow && (
            <RecentlyPlayed recentItems={recentItems} onSelect={handleRecentSelect} />
          )}
          {showFavorites ? (
            <FavoritesView
              tvFavorites={favoritesList}
              radioFavorites={radioFavoritesList}
              onSelectChannel={openTvPlayer}
              onSelectStation={handleSelectStation}
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
              onSelect={openTvPlayer}
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
              onGuestNotice={onGuestNotice}
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
              onSelect={handleSelectStation}
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
              onGuestNotice={onGuestNotice}
              getVoteSummary={(id) => votes.getSummaryFor("radio", id)}
              stats={stats}
            />
          )}
        </main>
      </div>
      {selectedChannel && (
        <VideoPlayer
          channel={selectedChannel}
          minimized={!tvModalOpen}
          onMinimize={() => setTvModalOpen(false)}
          onExpand={() => setTvModalOpen(true)}
          onClose={closeTvPlayer}
          isFavorite={isFavorite(selectedChannel.id)}
          onToggleFavorite={() => toggleFavorite(selectedChannel)}
          isGuest={isGuest}
          onLogin={() => setShowLogin(true)}
          onGuestNotice={onGuestNotice}
          myVotes={votes.getMyVotesFor("tv", selectedChannel.id)}
          voteSummary={votes.getSummaryFor("tv", selectedChannel.id)}
          onVote={votes.submitVote}
        />
      )}
      {selectedStation && (
        <RadioPlayer
          station={selectedStation}
          audioRef={radioAudioRef}
          minimized={!radioModalOpen}
          onMinimize={() => setRadioModalOpen(false)}
          onClose={stopRadio}
          isFavorite={isRadioFavorite(selectedStation.id)}
          onToggleFavorite={() => toggleRadioFavorite(selectedStation)}
          isGuest={isGuest}
          onLogin={() => setShowLogin(true)}
          onGuestNotice={onGuestNotice}
          myVotes={votes.getMyVotesFor("radio", selectedStation.id)}
          voteSummary={votes.getSummaryFor("radio", selectedStation.id)}
          onVote={votes.submitVote}
        />
      )}
      {nowPlaying && !nowPlaying.modalOpen && (
        <MiniPlayer
          station={nowPlaying.station}
          audioRef={radioAudioRef}
          onExpand={() => setRadioModalOpen(true)}
          onStop={stopRadio}
        />
      )}
      <GuestNoticeToast
        message={guestNotice}
        onDismiss={dismissGuestNotice}
        onSignIn={guestNoticeSignIn}
      />
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
        <span className="footer-version">v2.1.0</span>
      </footer>
    </>
  );
}
