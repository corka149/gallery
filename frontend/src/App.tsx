import { RouteSectionProps } from "@solidjs/router";
import type { Component } from "solid-js";
import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";

const App: Component<RouteSectionProps<unknown>> = (props) => {
  return (
    <>
      <div class="bg-amber-400 flex justify-center" style={{ "min-height": "10vh" }}>
        <Navbar />
      </div>
      <main class="mx-auto max-w-xl mt-4" style={{"min-height": "80vh"}}>{props.children}</main>
      <div class="bg-gray-500" style="min-height: 5vh">
        <div class="mx-auto max-w-xl">
          <Footer />
        </div>
      </div>
    </>
  );
};

export default App;
