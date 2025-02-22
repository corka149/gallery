import logo from "../assets/logo.png";

const Navbar = () => {
  return (
    <nav class="flex items-center justify-between w-2xl mx-4">
      <img src={logo} alt="Sun rises behind a mountain"
        class="max-h-24"
      />
      <span class="text-center text-xl my-4 font-bold italic text-amber-900">Gallery</span>
      <ul class="flex space-x-4">
        <li>
          <a href="/" class="underline text-amber-900">Home</a>
        </li>
        <li>
          <a href="/login" class="underline text-amber-900">Login</a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
