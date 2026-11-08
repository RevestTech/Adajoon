import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchRadioMap, fetchRadioMapRide } from "../api/radio";

describe("radio map API helpers", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchRadioMap builds bbox query", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ type: "stations", items: [], zoom: 8 }),
    });

    const data = await fetchRadioMap({
      bbox: "-10,40,10,50",
      zoom: 8,
      workingOnly: true,
    });

    expect(global.fetch).toHaveBeenCalledOnce();
    const url = global.fetch.mock.calls[0][0];
    expect(url).toContain("/api/radio/map?");
    expect(url).toContain("bbox=-10%2C40%2C10%2C50");
    expect(url).toContain("zoom=8");
    expect(url).toContain("working_only=true");
    expect(data.type).toBe("stations");
  });

  it("fetchRadioMapRide includes optional center", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: "abc", name: "Test FM", url: "https://example.com/stream" }),
    });

    const station = await fetchRadioMapRide({ lat: 48.8, lng: 2.3 });

    const url = global.fetch.mock.calls[0][0];
    expect(url).toContain("/api/radio/map/ride?");
    expect(url).toContain("lat=48.8");
    expect(url).toContain("lng=2.3");
    expect(station.name).toBe("Test FM");
  });

  it("fetchRadioMapRide throws on 404", async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404 });
    await expect(fetchRadioMapRide({})).rejects.toThrow(/No station found/);
  });
});
