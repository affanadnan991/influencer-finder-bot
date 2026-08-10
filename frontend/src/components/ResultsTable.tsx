"use client";

import { useState } from "react";
import type { ProfileResult } from "@/lib/api";
import { getDownloadUrl } from "@/lib/api";

interface ResultsTableProps {
  results: ProfileResult[];
  jobId: string;
}

type SortKey = "username" | "niche" | "score";

export default function ResultsTable({ results, jobId }: ResultsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortAsc, setSortAsc] = useState(false);
  const [search, setSearch] = useState("");

  if (results.length === 0) {
    return (
      <div className="text-center py-10 animate-fade-in">
        <svg className="w-12 h-12 mx-auto text-gray-700 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p className="text-gray-500">No matching profiles found.</p>
        <p className="text-xs text-gray-600 mt-1">Try different keywords or a larger max followings count.</p>
      </div>
    );
  }

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === "username"); // username asc by default, others desc
    }
  };

  const filtered = results.filter(
    (p) =>
      p.username.toLowerCase().includes(search.toLowerCase()) ||
      p.niche.toLowerCase().includes(search.toLowerCase())
  );

  const sorted = [...filtered].sort((a, b) => {
    let cmp = 0;
    if (sortKey === "username") cmp = a.username.localeCompare(b.username);
    else if (sortKey === "niche") cmp = a.niche.localeCompare(b.niche);
    else cmp = a.score - b.score;
    return sortAsc ? cmp : -cmp;
  });

  const SortIcon = ({ active, asc }: { active: boolean; asc: boolean }) => (
    <svg className={`w-3 h-3 inline ml-1 ${active ? "text-violet-400" : "text-gray-600"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d={asc ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
    </svg>
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm font-medium text-gray-300">
          <span className="text-white font-bold">{results.length}</span> profiles found
        </h3>
        <div className="flex items-center gap-2">
          {/* Search filter */}
          <div className="relative">
            <svg className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter..."
              className="w-40 pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            />
          </div>
          <a
            href={getDownloadUrl(jobId)}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors shadow-md shadow-violet-600/20"
            download
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            CSV
          </a>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden border border-gray-700 rounded-xl">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/80">
              <th className="text-left px-4 py-3 text-gray-500 font-medium w-12">#</th>
              <th
                className="text-left px-4 py-3 text-gray-400 font-medium cursor-pointer hover:text-gray-200 transition-colors select-none"
                onClick={() => toggleSort("username")}
              >
                Username
                <SortIcon active={sortKey === "username"} asc={sortAsc && sortKey === "username"} />
              </th>
              <th
                className="text-left px-4 py-3 text-gray-400 font-medium cursor-pointer hover:text-gray-200 transition-colors select-none"
                onClick={() => toggleSort("niche")}
              >
                Keyword
                <SortIcon active={sortKey === "niche"} asc={sortAsc && sortKey === "niche"} />
              </th>
              <th
                className="text-left px-4 py-3 text-gray-400 font-medium cursor-pointer hover:text-gray-200 transition-colors select-none w-20"
                onClick={() => toggleSort("score")}
              >
                Score
                <SortIcon active={sortKey === "score"} asc={sortAsc && sortKey === "score"} />
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((profile, idx) => (
              <tr
                key={profile.username}
                className="border-t border-gray-800/50 hover:bg-gray-800/40 transition-colors animate-slide-in"
                style={{ animationDelay: `${Math.min(idx * 30, 300)}ms` }}
              >
                <td className="px-4 py-3 text-gray-600 tabular-nums">{idx + 1}</td>
                <td className="px-4 py-3">
                  <a
                    href={profile.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-violet-400 hover:text-violet-300 transition-colors"
                  >
                    @{profile.username}
                  </a>
                </td>
                <td className="px-4 py-3">
                  {profile.niche ? (
                    <span className="inline-block px-2.5 py-0.5 bg-violet-900/40 text-violet-300 text-xs rounded-full border border-violet-800/30">
                      {profile.niche}
                    </span>
                  ) : (
                    <span className="text-gray-700">&mdash;</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`tabular-nums font-medium ${
                    profile.score >= 9 ? "text-green-400" :
                    profile.score >= 6 ? "text-violet-400" :
                    "text-gray-400"
                  }`}>
                    {profile.score}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {sorted.length === 0 && search && (
          <div className="text-center py-6 text-gray-500 text-sm">
            No results match &ldquo;{search}&rdquo;
          </div>
        )}
      </div>

      <p className="text-xs text-gray-600 text-right">
        Showing {sorted.length} of {results.length}
      </p>
    </div>
  );
}
