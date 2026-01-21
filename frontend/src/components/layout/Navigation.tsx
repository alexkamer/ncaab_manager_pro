'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Trophy, Users, User, BarChart3, TrendingUp } from 'lucide-react';

const navItems = [
  { href: '/', label: 'Games', icon: Trophy },
  { href: '/teams', label: 'Teams', icon: Users },
  { href: '/players', label: 'Players', icon: User },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/betting', label: 'Betting', icon: TrendingUp },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <Trophy className="w-8 h-8 text-blue-500" />
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              NCAA Analytics
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
