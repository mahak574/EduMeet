import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useAuthStore } from '../../stores/authStore';
import { X, Mail, ShieldCheck, ArrowRight, RefreshCw, CheckCircle2, Sparkles } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const GOOGLE_CLIENT_ID =
  (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID ||
  '915728215365-0sfpmtc038889gau3tafrvrf6gfrcrgu.apps.googleusercontent.com';

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { sendOtp, verifyOtp, googleLogin, demoLogin } = useAuthStore();
  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [googleScriptLoaded, setGoogleScriptLoaded] = useState(false);

  const googleBtnContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (resendCooldown > 0) {
      timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  // Initialize Google Identity Services when on the email step
  useEffect(() => {
    if (!isOpen || step !== 'email') return;

    let timer: any;
    const initGsi = () => {
      const google = (window as any).google;
      if (google?.accounts?.id && googleBtnContainerRef.current) {
        try {
          google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: async (response: any) => {
              if (response?.credential) {
                setLoading(true);
                setErrorMessage(null);
                try {
                  await googleLogin(response.credential);
                  onClose();
                } catch (err: any) {
                  setErrorMessage(err.message || 'Google authentication failed. Please try again.');
                } finally {
                  setLoading(false);
                }
              }
            },
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          // Clear previous render to avoid duplicate buttons
          googleBtnContainerRef.current.innerHTML = '';
          google.accounts.id.renderButton(googleBtnContainerRef.current, {
            type: 'standard',
            theme: 'filled_black',
            size: 'large',
            text: 'signin_with',
            shape: 'pill',
            width: 360,
            logo_alignment: 'left',
          });
          setGoogleScriptLoaded(true);
        } catch (err) {
          console.warn('Google Identity initialization error:', err);
        }
      }
    };

    initGsi();
    timer = setInterval(initGsi, 400);
    const stopTimer = setTimeout(() => clearInterval(timer), 4000);

    return () => {
      clearInterval(timer);
      clearTimeout(stopTimer);
    };
  }, [isOpen, step, googleLogin, onClose]);

  if (!isOpen) return null;

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }
    if (!ageConfirmed) {
      setErrorMessage('You must confirm you are at least 18 years old to join.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      // In development, uses Cloudflare test token accepted by backend
      const devTurnstileToken = '1x00000000000000000000AA';
      await sendOtp(email, devTurnstileToken);
      setStep('otp');
      setResendCooldown(60);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join('');
    if (code.length !== 6) {
      setErrorMessage('Please enter all 6 digits of the verification code.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      await verifyOtp(email, code);
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) {
      value = value.slice(-1);
    }
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleGoogleFallbackClick = () => {
    const google = (window as any).google;
    if (google?.accounts?.id) {
      google.accounts.id.prompt();
    } else {
      setErrorMessage('Google Identity is still loading. Please wait a moment or try refreshing.');
    }
  };

  const handleDemoLoginClick = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      await demoLogin();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Demo sign in failed.');
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-md p-6 glass-panel rounded-2xl border border-white/10 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/50 transition-colors"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 mb-3">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold font-sans text-white">
            {step === 'email' ? 'Welcome to EduMeet' : 'Enter Verification Code'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {step === 'email'
              ? 'Join the global reciprocal peer teaching network'
              : `We sent a 6-digit code to ${email}`}
          </p>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
            {errorMessage}
          </div>
        )}

        {step === 'email' ? (
          <div className="space-y-4">
            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label htmlFor="email-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="email-input"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="student@university.edu"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  />
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <input
                  id="age-confirm"
                  type="checkbox"
                  checked={ageConfirmed}
                  onChange={(e) => setAgeConfirmed(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-brand-500 focus:ring-brand-500 focus:ring-offset-slate-900 cursor-pointer"
                />
                <label htmlFor="age-confirm" className="text-xs text-slate-300 select-none cursor-pointer">
                  I confirm that I am at least 18 years old and agree to the platform community guidelines and mutual peer teaching policies.
                </label>
              </div>

              <button
                type="submit"
                disabled={loading || !ageConfirmed || !email}
                className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <>Continue with Email <ArrowRight className="w-4 h-4" /></>}
              </button>
            </form>

            <div className="relative my-4 text-center">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800"></div></div>
              <span className="relative px-3 bg-slate-950 text-xs text-slate-500">or continue with</span>
            </div>

            {/* Authentic Google Sign-In with Google Identity Services */}
            <div className="w-full flex flex-col items-center justify-center min-h-[44px]">
              <div
                ref={googleBtnContainerRef}
                className="w-full flex justify-center"
              />
              {!googleScriptLoaded && (
                <button
                  type="button"
                  onClick={handleGoogleFallbackClick}
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-sm font-medium transition-all flex items-center justify-center gap-2.5 cursor-pointer shadow-sm"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.2 9 5 12 5z"/>
                    <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5.1 3.7-8.8z"/>
                    <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3 0-.8.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.2c0 2.8.7 5.5 1.9 7.9l3.7-2.9z"/>
                    <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.2-6.4-5.2L1.9 16c1.8 3.7 5.6 7 10.1 7z"/>
                  </svg>
                  <span>Sign in with Google</span>
                </button>
              )}
            </div>

            {/* Distinct 1-Click Demo Login for testing */}
            <div className="pt-2 border-t border-slate-900">
              <button
                type="button"
                onClick={handleDemoLoginClick}
                disabled={loading}
                className="w-full py-2 px-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Quick Demo Account (Alex Rivera)</span>
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 text-center mb-3">
                6-Digit Security Code
              </label>
              <div className="flex justify-between gap-2">
                {otp.map((digit, idx) => (
                  <input
                    key={idx}
                    id={`otp-input-${idx}`}
                    type="text"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(idx, e.target.value)}
                    className="w-12 h-12 text-center text-xl font-bold rounded-xl bg-slate-900 border border-slate-700 text-brand-400 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || otp.join('').length !== 6}
              className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <>Verify & Complete <CheckCircle2 className="w-4 h-4" /></>}
            </button>

            <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
              <button
                type="button"
                onClick={() => setStep('email')}
                className="hover:text-slate-200 transition-colors"
              >
                Change email
              </button>
              <button
                type="button"
                disabled={resendCooldown > 0 || loading}
                onClick={handleSendOtp}
                className="text-brand-400 hover:text-brand-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>,
    document.body
  );
};
