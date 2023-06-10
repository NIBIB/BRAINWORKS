/// <reference types="react-scripts" />

// Typescript recognizing mp4 files
declare module "*.mp4" {
  const src: string;
  export default src;
}

// Typescript recognizing window as an object
declare global {
  interface Window {}
}
