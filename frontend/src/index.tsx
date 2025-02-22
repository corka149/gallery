/* @refresh reload */
import { render } from "solid-js/web";
import { Route, Router } from "@solidjs/router";

import "./index.css";
import App from "./App.jsx";
import Home from "./pages/home/Home.jsx";
import Login from "./pages/login/Login.jsx";

const root = document.getElementById("root");

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error(
    "Root element not found. Did you forget to add it to your index.html? Or maybe the id attribute got misspelled?"
  );
}

render(() => <Router root={App}>
  <Route path="/" component={Home} />
  <Route path="/login" component={Login} />
</Router>, root!);
