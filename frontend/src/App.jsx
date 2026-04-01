import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChannelGrid from "./components/ChannelGrid";
import VideoPlayer from "./components/VideoPlayer";
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
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  const [selectedChannel, setSelectedChannel] = useState(null);

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
      // Metadata fetch may fail during initial sync — that's okay
    }
  }, []);

  const loadChannels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchChannels({
        query: search || undefined,
        category: activeCategory || undefined,
        country: activeCountry || undefined,
        page,
      });
      setChannels(data.channels);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (e) {
      setError("Unable to load channels. The server may still be syncing data — try again in a moment.");
    } finally {
      setLoading(false);
    }
  }, [search, activeCategory, activeCountry, page]);

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
  }, [search, activeCategory, activeCountry]);

  const clearFilter = (type) => {
    if (type === "category") setActiveCategory(null);
    if (type === "country") setActiveCountry(null);
    if (type === "search") setSearch("");
  };

  return (
    <>
      <Header search={search} onSearch={setSearch} stats={stats} />
      <div className="layout">
        <Sidebar
          categories={categories}
          countries={countries}
          activeCategory={activeCategory}
          activeCountry={activeCountry}
          onSelectCategory={(id) => setActiveCategory(id === activeCategory ? null : id)}
          onSelectCountry={(code) => setActiveCountry(code === activeCountry ? null : code)}
        />
        <main className="main-content">
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
            onClearFilter={clearFilter}
            onRetry={loadChannels}
          />
        </main>
      </div>
      {selectedChannel && (
        <VideoPlayer
          channel={selectedChannel}
          onClose={() => setSelectedChannel(null)}
        />
      )}
    </>
  );
}
