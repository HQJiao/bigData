<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-body);
  line-height: var(--lh-relaxed);
  background: var(--color-parchment);
  color: var(--color-near-black);
  -webkit-font-smoothing: antialiased;
}

#app {
  height: 100vh;
}

h1, h2, h3, h4 {
  font-family: var(--font-serif);
  font-weight: 500;
  line-height: var(--lh-heading);
}

a {
  color: var(--color-terracotta);
  text-decoration: none;
}

a:hover {
  color: var(--color-coral);
}

input, textarea, select, button {
  font-family: var(--font-sans);
  font-size: var(--text-body);
}
</style>
