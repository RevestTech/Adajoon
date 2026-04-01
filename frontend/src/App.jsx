import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChannelGrid from "./components/ChannelGrid";
import VideoPlayer from "./components/VideoPlayer";
import useFavorites from "./hooks/useFavorites";
import { fetchChannels, fetchCategories, fetchCountries, fetchStats } from "./api/channels";

export default function App() {
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

  const { favoritesList, favoritesCount, toggleFavorite, isFavorite } = useFavorites();

  const loadMeta = useCallback(async () => {
    try {
      const [cats, ctrs, st] = await Promise.all([
        fetchCategories(),
        fetchCountries(),
        fetchStats(),
      ]);
      setCategories(cats);
      setCountries(ctrs);
      setStats(st);
    } catch {
      // Metadata fetch may fail during initial sync
    }
  }, []);

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
      setError("Unable to load channels. The server may still be syncing data — try again in a moment.");
    } finally {
      setLoading(false);
    }
  }, [search, activeCategory, activeCountry, liveOnly, page, showFavorites]);

  useEffect(() => {
    loadMeta();
    const interval = setInterval(loadMeta, 30000);
    return () => clearInterval(interval);
  }, [loadMeta]);

  useEffect(() => {
    loadChannels();
  }, [loadChannels]);

  useEffect(() => {
    setPage(1);
  }, [search, activeCategory, activeCountry, showFavorites, liveOnly]);

  const displayedChannels = showFavorites ? favoritesList : channels;
  const displayedTotal = showFavorites ? favoritesCount : total;
  const displayedTotalPages = showFavorites ? 1 : totalPages;

  const clearFilter = (type) => {
    if (type === "category") setActiveCategory(null);
    if (type === "country") setActiveCountry(null);
    if (type === "search") setSearch("");
    if (type === "favorites") setShowFavorites(false);
    if (type === "liveOnly") setLiveOnly(false);
  };

  const handleToggleFavorites = () => {
    setShowFavorites((prev) => !prev);
    if (!showFavorites) {
      setActiveCategory(null);
      setActiveCountry(null);
      setSearch("");
    }
  };

  return (
    <>
      <Header
        search={search}
        onSearch={(val) => { setSearch(val); setShowFavorites(false); }}
        stats={stats}
        favoritesCount={favoritesCount}
        showFavorites={showFavorites}
        onToggleFavorites={handleToggleFavorites}
        liveOnly={liveOnly}
        onToggleLiveOnly={() => setLiveOnly((v) => !v)}
      />
      <div className="layout">
        <Sidebar
          categories={categories}
          countries={countries}
          activeCategory={activeCategory}
          activeCountry={activeCountry}
          onSelectCategory={(id) => { setActiveCategory(id === activeCategory ? null : id); setShowFavorites(false); }}
          onSelectCountry={(code) => { setActiveCountry(code === activeCountry ? null : code); setShowFavorites(false); }}
          favoritesCount={favoritesCount}
          showFavorites={showFavorites}
          onToggleFavorites={handleToggleFavorites}
        />
        <main className="main-content">
          <ChannelGrid
            channels={displayedChannels}
            loading={!showFavorites && loading}
            error={!showFavorites ? error : null}
            total={displayedTotal}
            page={page}
            totalPages={displayedTotalPages}
            onPageChange={setPage}
            onSelect={setSelectedChannel}
            activeCategory={activeCategory}
            activeCountry={activeCountry}
            search={search}
            showFavorites={showFavorites}
            liveOnly={liveOnly}
            onClearFilter={clearFilter}
            onRetry={loadChannels}
            isFavorite={isFavorite}
            onToggleFavorite={toggleFavorite}
          />
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
    </>
  );
}
