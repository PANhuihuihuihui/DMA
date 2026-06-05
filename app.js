const header = document.querySelector("[data-header]");
const menuButton = document.querySelector("[data-menu-button]");
const modal = document.querySelector("[data-modal]");
const toast = document.querySelector("[data-toast]");
const form = document.querySelector("[data-pilot-form]");
const openModalButtons = document.querySelectorAll("[data-open-modal]");
const closeModalButton = document.querySelector("[data-close-modal]");

const setModal = (open) => {
  modal.hidden = !open;
  document.body.style.overflow = open ? "hidden" : "";
  if (open) {
    const firstInput = modal.querySelector("input");
    window.setTimeout(() => firstInput?.focus(), 80);
  }
};

openModalButtons.forEach((button) => {
  button.addEventListener("click", () => setModal(true));
});

closeModalButton.addEventListener("click", () => setModal(false));

modal.addEventListener("click", (event) => {
  if (event.target === modal) {
    setModal(false);
  }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modal.hidden) {
    setModal(false);
  }
});

menuButton.addEventListener("click", () => {
  const isOpen = header.classList.toggle("menu-open");
  menuButton.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
});

document.querySelectorAll(".nav-links a").forEach((link) => {
  link.addEventListener("click", () => {
    header.classList.remove("menu-open");
    menuButton.setAttribute("aria-label", "Open navigation");
  });
});

window.addEventListener("scroll", () => {
  header.classList.toggle("is-scrolled", window.scrollY > 12);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  window.localStorage.setItem("localpilot-pilot-request", JSON.stringify(data));
  form.reset();
  setModal(false);
  toast.hidden = false;
  window.setTimeout(() => {
    toast.hidden = true;
  }, 3800);
});
