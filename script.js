const weddingDate = new Date("2026-06-28T11:00:00+09:00");

const defaultMessages = [
  { writer: "호호", message: "두 분의 결혼을 진심으로 축하해요. 오래오래 행복만 하기!" },
  { writer: "라몽", message: "선남선녀 너무 축하해요. 서로의 가장 좋은 편이 되어주세요." },
  { writer: "맂이", message: "너무 예쁜 두 사람, 새로운 시작을 응원합니다." },
];

const copyResult = document.querySelector("#copyResult");
const messageList = document.querySelector("#messageList");
const guestbookDialog = document.querySelector("#guestbookDialog");
const rsvpDialog = document.querySelector("#rsvpDialog");
const photoDialog = document.querySelector("#photoDialog");
const photoDialogImage = document.querySelector("#photoDialog img");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const cover = document.querySelector(".cover");
const greetingSection = document.querySelector(".greeting");
const scrollCue = document.querySelector("#scrollCue");
const kakaoMapContainer = document.querySelector("#kakaoMap");
const kakaoMapAppKey = document.querySelector("meta[name='kakao-map-app-key']")?.content.trim() || window.KAKAO_MAP_APP_KEY || "";

let revealObserver = null;
let coverScrollDebt = 0;
let coverTouchY = 0;
let coverTransitioning = false;
let coverResetTimer = null;
let kakaoMapSdkPromise = null;

const coverScrollThreshold = 180;

const revealElement = (element, delay = 0) => {
  if (!element || element.classList.contains("fade-up")) {
    return;
  }

  element.classList.add("fade-up");
  element.style.transitionDelay = `${delay}ms`;

  if (prefersReducedMotion || !revealObserver) {
    element.classList.add("in-view");
    return;
  }

  revealObserver.observe(element);
};

const setupRevealAnimations = () => {
  if (!prefersReducedMotion && "IntersectionObserver" in window) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }

          entry.target.classList.add("in-view");
          revealObserver.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
  }

  const revealTargets = document.querySelectorAll(
    [
      ".section h1",
      ".section h2",
      ".wide-photo",
      ".poem",
      ".time-grid",
      ".d-day",
      ".event-line",
      ".divider",
      ".calendar-section h3",
      ".calendar",
      ".map-preview",
      ".map-buttons",
      ".location-text",
      ".photo-grid",
      ".chevron",
      ".notice dl > div",
      ".account-box",
      ".rsvp p",
      ".rsvp .line-button",
      ".share-buttons",
    ].join(", "),
  );

  revealTargets.forEach((element, index) => {
    revealElement(element, Math.min((index % 4) * 80, 240));
  });
};

const isAtCoverStart = () => window.scrollY <= Math.min(24, cover.offsetHeight * 0.04);

const setCoverPull = () => {
  const progress = Math.min(coverScrollDebt / coverScrollThreshold, 1);
  cover.style.setProperty("--cover-scale", (1.035 + progress * 0.018).toFixed(3));
  cover.style.setProperty("--cover-shift", `${Math.round(progress * -14)}px`);
  cover.classList.toggle("is-pulling", progress > 0 && !coverTransitioning);
};

const resetCoverPull = () => {
  if (coverTransitioning) {
    return;
  }

  coverScrollDebt = 0;
  cover.style.removeProperty("--cover-scale");
  cover.style.removeProperty("--cover-shift");
  cover.classList.remove("is-pulling");
};

const movePastCover = () => {
  if (coverTransitioning) {
    return;
  }

  coverTransitioning = true;
  coverScrollDebt = coverScrollThreshold;
  setCoverPull();
  cover.classList.remove("is-pulling");
  cover.classList.add("is-leaving");

  window.setTimeout(() => {
    greetingSection.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" });
  }, prefersReducedMotion ? 0 : 80);

  window.setTimeout(() => {
    cover.classList.remove("is-leaving");
    coverTransitioning = false;
    resetCoverPull();
  }, prefersReducedMotion ? 120 : 1100);
};

const absorbCoverScroll = (deltaY) => {
  if (deltaY <= 0 || prefersReducedMotion || !isAtCoverStart() || coverTransitioning) {
    if (deltaY < 0) {
      resetCoverPull();
    }

    return false;
  }

  coverScrollDebt = Math.min(coverScrollDebt + deltaY, coverScrollThreshold);
  setCoverPull();

  window.clearTimeout(coverResetTimer);
  coverResetTimer = window.setTimeout(resetCoverPull, 620);

  if (coverScrollDebt >= coverScrollThreshold) {
    window.clearTimeout(coverResetTimer);
    movePastCover();
  }

  return true;
};

const setupCoverScrollGate = () => {
  window.addEventListener(
    "wheel",
    (event) => {
      if (!absorbCoverScroll(event.deltaY)) {
        return;
      }

      event.preventDefault();
    },
    { passive: false },
  );

  window.addEventListener(
    "touchstart",
    (event) => {
      coverTouchY = event.touches[0]?.clientY || 0;
    },
    { passive: true },
  );

  window.addEventListener(
    "touchmove",
    (event) => {
      const currentY = event.touches[0]?.clientY || coverTouchY;
      const deltaY = coverTouchY - currentY;
      coverTouchY = currentY;

      if (!absorbCoverScroll(deltaY * 1.35)) {
        return;
      }

      event.preventDefault();
    },
    { passive: false },
  );

  window.addEventListener("keydown", (event) => {
    if (!["ArrowDown", "PageDown", "Space"].includes(event.code) || !isAtCoverStart()) {
      return;
    }

    event.preventDefault();
    movePastCover();
  });

  scrollCue.addEventListener("click", movePastCover);
};

const loadKakaoMapSdk = () => {
  if (!kakaoMapAppKey) {
    return Promise.reject(new Error("Kakao Maps JavaScript key is not configured."));
  }

  if (window.kakao?.maps) {
    return new Promise((resolve) => window.kakao.maps.load(resolve));
  }

  if (kakaoMapSdkPromise) {
    return kakaoMapSdkPromise;
  }

  kakaoMapSdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(kakaoMapAppKey)}&libraries=services,clusterer&autoload=false`;
    script.async = true;
    script.onload = () => {
      if (!window.kakao?.maps) {
        reject(new Error("Kakao Maps SDK did not initialize."));
        return;
      }

      window.kakao.maps.load(resolve);
    };
    script.onerror = () => reject(new Error("Kakao Maps SDK failed to load."));
    document.head.append(script);
  });

  return kakaoMapSdkPromise;
};

const setupKakaoMap = async () => {
  if (!kakaoMapContainer) {
    return;
  }

  try {
    await loadKakaoMapSdk();

    const latitude = Number(kakaoMapContainer.dataset.lat);
    const longitude = Number(kakaoMapContainer.dataset.lng);
    const level = Number(kakaoMapContainer.dataset.level || 5);
    const title = kakaoMapContainer.dataset.title || "예식장";
    const center = new window.kakao.maps.LatLng(latitude, longitude);
    const map = new window.kakao.maps.Map(kakaoMapContainer, {
      center,
      level,
      draggable: true,
      scrollwheel: false,
    });
    const marker = new window.kakao.maps.Marker({ position: center, title });
    const overlay = new window.kakao.maps.CustomOverlay({
      position: center,
      yAnchor: 2.45,
      content: `<span class="kakao-map-label">${title}</span>`,
    });

    marker.setMap(map);
    overlay.setMap(map);
    kakaoMapContainer.classList.add("is-loaded");

    window.setTimeout(() => {
      map.relayout();
      map.setCenter(center);
    }, 80);
  } catch {
    kakaoMapContainer.classList.add("is-fallback");
  }
};

const setCountdown = () => {
  const diff = weddingDate.getTime() - Date.now();
  const safeDiff = Math.max(diff, 0);
  const totalSeconds = Math.floor(safeDiff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  document.querySelector("#daysLeft").textContent = days;
  document.querySelector("#hoursLeft").textContent = hours;
  document.querySelector("#minutesLeft").textContent = minutes;
  document.querySelector("#secondsLeft").textContent = seconds;
  document.querySelector("#dateMessage").textContent = diff > 0 ? `${days + 1}일 남았습니다.` : "오늘입니다.";
};

const getMessages = () => {
  const saved = JSON.parse(localStorage.getItem("wedding-messages") || "[]");
  return saved.length ? saved : defaultMessages;
};

const renderMessages = (showAll = false) => {
  const messages = getMessages();
  const visibleMessages = showAll ? messages : messages.slice(-3);
  messageList.innerHTML = "";

  visibleMessages.forEach((item, index) => {
    const li = document.createElement("li");
    const actions = document.createElement("span");
    const strong = document.createElement("strong");
    const p = document.createElement("p");
    actions.className = "message-actions";
    actions.setAttribute("aria-hidden", "true");
    actions.innerHTML = '<span class="message-action edit"></span><span class="message-action delete"></span>';
    strong.textContent = `from. ${item.writer}`;
    p.textContent = item.message;
    li.append(actions, strong, p);
    messageList.append(li);
    revealElement(li, Math.min(index * 70, 210));
  });
};

document.querySelector("#musicToggle").addEventListener("click", (event) => {
  const button = event.currentTarget;
  const isOn = button.classList.toggle("is-on");
  button.setAttribute("aria-pressed", String(isOn));
  button.setAttribute("aria-label", isOn ? "배경음악 끄기" : "배경음악 켜기");
});

document.querySelectorAll("[data-open='guestbook']").forEach((button) => {
  button.addEventListener("click", () => guestbookDialog.showModal());
});

document.querySelectorAll("[data-open='rsvp']").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#rsvpResult").textContent = "";
    rsvpDialog.showModal();
  });
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  });
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      copyResult.textContent = "계좌번호가 복사되었습니다.";
    } catch {
      copyResult.textContent = button.dataset.copy;
    }
  });
});

document.querySelectorAll("[data-photo]").forEach((button) => {
  button.addEventListener("click", () => {
    const image = button.querySelector("img");
    photoDialogImage.src = image.src;
    photoDialogImage.alt = image.alt || "확대된 웨딩 사진";
    photoDialog.showModal();
  });
});

document.querySelector("#messageForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  const saved = JSON.parse(localStorage.getItem("wedding-messages") || "[]");
  saved.push(data);
  localStorage.setItem("wedding-messages", JSON.stringify(saved));
  event.currentTarget.reset();
  guestbookDialog.close();
  renderMessages();
});

document.querySelector("#showAllMessages").addEventListener("click", () => {
  renderMessages(true);
});

document.querySelector("#rsvpForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  localStorage.setItem("wedding-rsvp", JSON.stringify(data));
  document.querySelector("#rsvpResult").textContent = `${data.name}님의 참석 의사가 저장되었습니다.`;
  event.currentTarget.reset();
});

document.querySelector("#copyLink").addEventListener("click", async () => {
  await navigator.clipboard.writeText(location.href);
  alert("링크가 복사되었습니다.");
});

document.querySelector("#shareButton").addEventListener("click", async () => {
  const shareData = {
    title: "민준♥서연 결혼합니다",
    text: "2026년 6월 28일 일요일 오전 11시, 아펠가모 반포점",
    url: location.href,
  };

  if (navigator.share) {
    await navigator.share(shareData);
    return;
  }

  await navigator.clipboard.writeText(location.href);
  alert("청첩장 링크가 복사되었습니다.");
});

setCountdown();
setInterval(setCountdown, 1000);
setupCoverScrollGate();
setupRevealAnimations();
setupKakaoMap();
renderMessages();
