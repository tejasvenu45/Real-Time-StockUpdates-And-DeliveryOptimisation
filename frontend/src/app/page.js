// src/app/page.js
'use client'

// import { useAuth } from '@/lib/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import Navbar from '@/components/ui/navbar'

export default function HomePage() {
  // const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  // useEffect(() => {
  //   if (!loading && isAuthenticated) {
  //     router.push('/dashboard')
  //   }
  // }, [loading, isAuthenticated, router])

  // if (loading) {
  //   return (
  //     <div className="min-h-screen flex items-center justify-center">
  //       <div className="text-center">
  //         <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
  //         <p className="mt-4 text-gray-600">Loading...</p>
  //       </div>
  //     </div>
  //   )
  // }

  

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <Badge className="mb-6 bg-blue-100 text-blue-800 border-blue-200 text-sm font-medium px-4 py-2">
              🚀 Trusted by 500+ Logistics Partners Across India
            </Badge>
            
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight">
              India's Leading
              <span className="text-blue-600 block"> Warehouse & Logistics</span>
              Management Platform
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-4xl mx-auto leading-relaxed">
              Powering efficient supply chains from Mumbai to Chennai. We serve retail giants, 
              e-commerce leaders, and growing businesses with AI-driven warehouse optimization 
              and end-to-end logistics solutions.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
              <Link href="/auth/signup">
                <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg font-semibold">
                  Start Free Trial
                </Button>
              </Link>
              <Link href="/auth/login">
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-blue-200 text-blue-700 hover:bg-blue-50 px-8 py-4 text-lg font-semibold">
                  Sign In
                </Button>
              </Link>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-blue-100">
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">500+</div>
                <div className="text-gray-700 font-medium">Warehouse Partners</div>
              </div>
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-blue-100">
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">₹5000Cr</div>
                <div className="text-gray-700 font-medium">Goods Managed</div>
              </div>
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-blue-100">
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">28</div>
                <div className="text-gray-700 font-medium">States Covered</div>
              </div>
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-blue-100">
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">99.8%</div>
                <div className="text-gray-700 font-medium">Delivery Success</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Core Services Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Complete Logistics Solutions
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From warehouse automation to last-mile delivery, we provide end-to-end 
              logistics technology that scales with your business growth.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            
            {/* Stock Management */}
            <Card className="group hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-gray-100">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center text-3xl mb-4 mx-auto group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  📦
                </div>
                <CardTitle className="text-xl font-bold">Smart Stock Management</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-gray-600 mb-6">
                  AI-powered inventory optimization with real-time tracking across 
                  multiple warehouses and retail locations.
                </CardDescription>
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-3"></span>
                    Real-time inventory tracking
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-3"></span>
                    Automated reorder alerts
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-3"></span>
                    Multi-location sync
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-3"></span>
                    Expiry date management
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Retail Management */}
            <Card className="group hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-gray-100">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-green-100 text-green-600 rounded-2xl flex items-center justify-center text-3xl mb-4 mx-auto group-hover:bg-green-600 group-hover:text-white transition-colors">
                  🏪
                </div>
                <CardTitle className="text-xl font-bold">Retail Management</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-gray-600 mb-6">
                  Comprehensive retail operations management for chains, franchises, 
                  and independent stores across India.
                </CardDescription>
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-green-600 rounded-full mr-3"></span>
                    Multi-store coordination
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-green-600 rounded-full mr-3"></span>
                    POS system integration
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-green-600 rounded-full mr-3"></span>
                    Staff management tools
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-green-600 rounded-full mr-3"></span>
                    Sales analytics dashboard
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Demand Forecasting */}
            <Card className="group hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-gray-100">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center text-3xl mb-4 mx-auto group-hover:bg-purple-600 group-hover:text-white transition-colors">
                  📊
                </div>
                <CardTitle className="text-xl font-bold">AI Demand Forecasting</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-gray-600 mb-6">
                  Machine learning algorithms predict demand patterns, seasonal trends, 
                  and optimize purchasing decisions.
                </CardDescription>
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-purple-600 rounded-full mr-3"></span>
                    Predictive analytics
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-purple-600 rounded-full mr-3"></span>
                    Seasonal trend analysis
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-purple-600 rounded-full mr-3"></span>
                    Market demand insights
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-purple-600 rounded-full mr-3"></span>
                    Automated procurement
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Route Optimization */}
            <Card className="group hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-gray-100">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 bg-orange-100 text-orange-600 rounded-2xl flex items-center justify-center text-3xl mb-4 mx-auto group-hover:bg-orange-600 group-hover:text-white transition-colors">
                  🚚
                </div>
                <CardTitle className="text-xl font-bold">Route Optimization</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-gray-600 mb-6">
                  Advanced algorithms optimize delivery routes, reduce fuel costs, 
                  and improve delivery time across pan-India operations.
                </CardDescription>
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-orange-600 rounded-full mr-3"></span>
                    Dynamic route planning
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-orange-600 rounded-full mr-3"></span>
                    Real-time tracking
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-orange-600 rounded-full mr-3"></span>
                    Fuel cost optimization
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="w-2 h-2 bg-orange-600 rounded-full mr-3"></span>
                    Delivery time prediction
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* About Section */}
      <div className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            
            {/* Left Content */}
            <div>
              <Badge className="mb-6 bg-blue-100 text-blue-800 border-blue-200">
                🏆 Industry Leader Since 2015
              </Badge>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8">
                Powering India's Supply Chain Revolution
              </h2>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                From tier-1 cities to remote villages, we've built India's most comprehensive 
                warehouse and logistics network. Our technology powers supply chains for 
                leading brands like Reliance, Big Bazaar, and thousands of growing businesses.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center font-bold text-lg">
                    ✓
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Pan-India Network</h4>
                    <p className="text-sm text-gray-600">1000+ warehouses across 28 states</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center font-bold text-lg">
                    ✓
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">AI-Powered Systems</h4>
                    <p className="text-sm text-gray-600">Machine learning optimization</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center font-bold text-lg">
                    ✓
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">GST Compliance</h4>
                    <p className="text-sm text-gray-600">Complete regulatory adherence</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center font-bold text-lg">
                    ✓
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">24/7 Support</h4>
                    <p className="text-sm text-gray-600">Dedicated customer success</p>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/auth/signup">
                  <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700">
                    Start Your Digital Transformation
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  Download Case Studies
                </Button>
              </div>
            </div>

            {/* Right Content - Warehouse Network Visual */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-8 rounded-3xl">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                  Our Warehouse Network
                </h3>
                <p className="text-gray-600">
                  Strategic locations ensuring 24-48 hour delivery across India
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white p-4 rounded-xl text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-1">Mumbai</div>
                  <div className="text-sm text-gray-500 mb-1">Western Hub</div>
                  <div className="text-xs text-blue-600 font-medium">15 Centers</div>
                </div>
                <div className="bg-white p-4 rounded-xl text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-1">Delhi NCR</div>
                  <div className="text-sm text-gray-500 mb-1">Northern Hub</div>
                  <div className="text-xs text-blue-600 font-medium">12 Centers</div>
                </div>
                <div className="bg-white p-4 rounded-xl text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-1">Bangalore</div>
                  <div className="text-sm text-gray-500 mb-1">Southern Hub</div>
                  <div className="text-xs text-blue-600 font-medium">8 Centers</div>
                </div>
                <div className="bg-white p-4 rounded-xl text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-1">Kolkata</div>
                  <div className="text-sm text-gray-500 mb-1">Eastern Hub</div>
                  <div className="text-xs text-blue-600 font-medium">6 Centers</div>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-xl">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium text-gray-700">Coverage</span>
                  <span className="text-blue-600 font-bold">98.5% of India</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '98.5%'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trusted Partners Section */}
      <div className="py-20 bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Trusted by India's Leading Retailers & E-commerce Giants
          </h2>
          <p className="text-xl text-blue-100 mb-12">
            Join the ecosystem of successful businesses optimizing their supply chains
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="bg-white bg-opacity-10 backdrop-blur-sm p-6 rounded-2xl hover:bg-opacity-20 transition-all">
              <div className="text-white font-bold text-lg mb-1">Reliance Retail</div>
              <div className="text-blue-100 text-sm">2000+ Stores</div>
              <div className="text-blue-200 text-xs mt-1">₹500Cr+ Managed</div>
            </div>
            <div className="bg-white bg-opacity-10 backdrop-blur-sm p-6 rounded-2xl hover:bg-opacity-20 transition-all">
              <div className="text-white font-bold text-lg mb-1">Big Bazaar</div>
              <div className="text-blue-100 text-sm">300+ Stores</div>
              <div className="text-blue-200 text-xs mt-1">₹200Cr+ Managed</div>
            </div>
            <div className="bg-white bg-opacity-10 backdrop-blur-sm p-6 rounded-2xl hover:bg-opacity-20 transition-all">
              <div className="text-white font-bold text-lg mb-1">Spencer's</div>
              <div className="text-blue-100 text-sm">150+ Stores</div>
              <div className="text-blue-200 text-xs mt-1">₹100Cr+ Managed</div>
            </div>
            <div className="bg-white bg-opacity-10 backdrop-blur-sm p-6 rounded-2xl hover:bg-opacity-20 transition-all">
              <div className="text-white font-bold text-lg mb-1">Metro Cash</div>
              <div className="text-blue-100 text-sm">75+ Stores</div>
              <div className="text-blue-200 text-xs mt-1">₹80Cr+ Managed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="py-24 bg-white">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8">
            Ready to Transform Your Logistics Operations?
          </h2>
          <p className="text-xl text-gray-600 mb-12">
            Join 500+ businesses already optimizing their supply chains with our platform. 
            Get started with a free trial and see results in your first week.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-8">
            <Link href="/auth/signup">
              <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg">
                Start Free 30-Day Trial
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto border-blue-200 text-blue-700 hover:bg-blue-50 px-8 py-4 text-lg">
              Schedule Live Demo
            </Button>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-center items-center gap-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              No credit card required
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              Setup in under 5 minutes
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              24/7 customer support
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
            
            {/* Company Info */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-6">
                <div className="bg-blue-600 text-white p-3 rounded-xl">
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 3a2 2 0 00-2 2v1.816a2 2 0 00.732 1.548l6.414 5.23a2 2 0 002.708 0l6.414-5.23A2 2 0 0020 6.816V5a2 2 0 00-2-2H4z"/>
                    <path d="M3 8.732l6.414 5.23a2 2 0 002.708 0L18 8.732V17a2 2 0 01-2 2H4a2 2 0 01-2-2V8.732z"/>
                  </svg>
                </div>
                <div>
                  <div className="text-xl font-bold">Warehouse Management</div>
                  <div className="text-blue-400 text-sm">Logistics Solutions</div>
                </div>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed mb-6">
                India's leading warehouse management and logistics platform, 
                powering efficient supply chains for retailers and e-commerce businesses across the nation.
              </p>
              <div className="flex space-x-4">
                <div className="w-10 h-10 bg-gray-800 hover:bg-blue-600 rounded-lg flex items-center justify-center cursor-pointer transition-colors">
                  <span className="text-sm">📧</span>
                </div>
                <div className="w-10 h-10 bg-gray-800 hover:bg-blue-600 rounded-lg flex items-center justify-center cursor-pointer transition-colors">
                  <span className="text-sm">📱</span>
                </div>
                <div className="w-10 h-10 bg-gray-800 hover:bg-blue-600 rounded-lg flex items-center justify-center cursor-pointer transition-colors">
                  <span className="text-sm">🌐</span>
                </div>
              </div>
            </div>
            
            {/* Solutions */}
            <div>
              <h3 className="font-semibold mb-6 text-lg">Solutions</h3>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Stock Management</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Retail Management</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Demand Forecasting</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Route Optimization</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Vendor Management</a></li>
              </ul>
            </div>
            
            {/* Company */}
            <div>
              <h3 className="font-semibold mb-6 text-lg">Company</h3>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Press</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Partners</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            
            {/* Support */}
            <div>
              <h3 className="font-semibold mb-6 text-lg">Support</h3>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-white transition-colors">System Status</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-sm text-gray-400 mb-4 md:mb-0">
                &copy; 2025 Warehouse Management Solutions. All rights reserved. 
                <span className="text-blue-400"> Built with ❤️ in India</span>
              </p>
              <div className="flex space-x-6 text-sm text-gray-400">
                <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-white transition-colors">Cookie Policy</a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}