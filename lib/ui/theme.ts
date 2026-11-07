/**
 * Design tokens — follows the SuperAsk (StartUp) Figma: indigo → violet.
 *
 *   #4F3FA8  indigo — brand, primary actions, user turns, links
 *   #9D8CF2  violet — accent: dots, fills, the light end of heading accents
 *   #FFFFFF  paper  — content surfaces
 *
 * The signature brand surface is the 135° indigo → violet gradient
 * (T.gradient). The light violet is decoration only, never small text on
 * white. Text that must read as "verified" uses T.tealText — a green kept for
 * its meaning, which clears WCAG AA on white. (The `teal*` token names predate
 * the palette change and are kept so components need no edit.)
 *
 * Semantic state colours (verified / review due / stale) stay distinct from
 * the brand: a freshness indicator that reads as "brand" defeats FR-64.
 *
 * Shadows are kept shallow deliberately — NFR-15 targets low-end Android, and
 * large blurred shadows are the cheapest way to make a page scroll badly.
 */
export const T = {
  sky: "#4F3FA8",
  skyDeep: "#3F3289",
  skyWash: "#F3F0FF",
  skyLine: "#D4CCF7",

  deep: "#4F3FA8",
  deepHover: "#3F3289",
  deepWash: "#F7F5FF",

  teal: "#9D8CF2",
  tealText: "#0A7D63",
  tealWash: "#ECFDF7",

  /** Dark surfaces: chat sidebar, features band. */
  slate: "#171936",
  /** Footer. */
  night: "#0C0B20",

  paper: "#FFFFFF",
  page: "#F8FAFC",
  /** Chat canvas behind the message cards. */
  canvas: "#EEF2F7",
  /** Alternate marketing section background. */
  mist: "#FAFBFC",

  ink: "#101828",
  inkSoft: "#4A5565",
  inkFaint: "#99A1AF",

  line: "#E8EDF2",
  lineSoft: "#F1F5F9",
  lineStrong: "#D0D5DD",

  green: "#0A7D63",
  greenWash: "#ECFDF7",

  /** Notice — amber, for the decline callout and review-due indicators. */
  notice: "#F79009",
  noticeText: "#B54708",
  noticeWash: "#FFFAEB",
  noticeLine: "#FEDF89",

  red: "#D92D20",
  redWash: "#FEF3F2",
  redLine: "#FECDCA",

  gradient: "linear-gradient(135deg,#4F3FA8,#6D5BD0)",

  shadowSm: "0 1px 4px rgba(0,0,0,0.07)",
  shadowMd: "0 2px 8px rgba(0,0,0,0.07)",
  shadowLg: "0 8px 32px rgba(79,63,168,0.12)",

  /** Focus ring, as a shadow, tinted with brand indigo. */
  ringSky: "0 0 0 3px rgba(79,63,168,0.18)",
} as const;

/** Height of the top bar in the chat app. */
export const BRAND_BAR_HEIGHT = 56;

export const fontStack =
  "'Inter', 'Noto Sans Khmer', system-ui, -apple-system, 'Segoe UI', sans-serif";

export const monoStack =
  "'IBM Plex Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace";
